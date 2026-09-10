"""Academy transport hardening and remote execution backend."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, TypeVar

from .base import ExecutionBackend

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from concurrent.futures import Executor

    from academy.handle import Handle

    from ..config import ResourceConfig
    from ..protocol import (
        DirListing,
        ExecRequest,
        ExecResult,
        FileContent,
        FileGet,
        FilePut,
        FileStat,
        HandshakeReport,
        ListDir,
    )
    from ..remote.agent import ExecutionAgent

logger = logging.getLogger("lassi_x.execution")

SEND_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
SEND_RETRY_ATTEMPTS = 5
SEND_RETRY_BASE_DELAY_S = 0.5
STALL_WARN_INTERVAL_S = 60.0
CALL_TIMEOUT_S = 300.0
SHUTDOWN_TIMEOUT_S = 60.0
DEAD_AFTER_TIMEOUTS = 2
HEARTBEAT_INTERVAL_S = 5.0
HEARTBEAT_MISSES = 2
HEARTBEAT_TIMEOUT_S = 4.0
PAUSE_MAX_S = 900.0
_ARGV_LOG_LIMIT = 160
ResultT = TypeVar("ResultT")

def _disable_academy_stream_deadline(transport: Any) -> None:
    """Remove aiohttp's total deadline from Academy's long-lived SSE stream.

    Academy 0.4 creates its HTTP session with aiohttp's five-minute default
    total timeout. That deadline also covers the hosted exchange's event
    stream, so a healthy multi-minute run can silently lose its response
    listener. The hosted exchange currently requires Academy 0.4; adjust each
    new transport before the listener starts while retaining explicit timeout
    limits on individual LASSI-X operations.

    Args:
        transport: Newly created Academy HTTP exchange transport.

    """
    import aiohttp  # noqa: PLC0415

    transport._session._timeout = aiohttp.ClientTimeout(  # noqa: SLF001
        total=None,
        sock_connect=60,
        sock_read=None,
    )

def _add_academy_send_retry(
    transport: Any,
    *,
    attempts: int = SEND_RETRY_ATTEMPTS,
    base_delay_s: float = SEND_RETRY_BASE_DELAY_S,
) -> None:
    """Retry hosted-exchange sends that fail with a transient HTTP error.

    Academy returns every action result by sending a response message through
    the exchange, and shields that send from cancellation without retrying it
    (``academy/runtime.py`` ``_send_response``). A single 5xx from the hosted
    exchange therefore discards a response the agent already computed. Because
    no call in :class:`AcademyExecutionBackend` bounds its await, the caller
    then blocks forever: one 502 wedged a 3mm run until the suite-level
    timeout reaped the process nearly two hours later.

    Only transport-level failures are retried. Academy maps mailbox
    termination, unknown entities, and authorization failures to their own
    exceptions before ``raise_for_status`` runs, so those propagate on the
    first attempt rather than being hidden behind five rounds of backoff.

    Retrying a send is not perfectly idempotent -- a 504 can mean the exchange
    accepted the message and failed only while reporting that -- so a peer may
    observe a duplicate. Academy routes responses by request tag and the
    requester resolves the first one it sees, which makes a duplicate response
    far cheaper than a lost one.

    Args:
        transport: Newly created Academy HTTP exchange transport.
        attempts: Total send attempts, including the first.
        base_delay_s: Initial backoff in seconds, doubled after each failure.

    """
    import aiohttp  # noqa: PLC0415

    send = transport.send

    async def send_with_retry(message: Any) -> None:
        delay = base_delay_s
        for attempt in range(1, attempts + 1):
            try:
                await send(message)
            except (
                aiohttp.ClientConnectionError,
                aiohttp.ClientResponseError,
            ) as exc:
                retryable = (
                    isinstance(exc, aiohttp.ClientConnectionError)
                    or exc.status in SEND_RETRY_STATUSES
                )
                if not retryable or attempt == attempts:
                    raise
                logger.warning(
                    "Academy exchange send failed (attempt %d/%d): %s; retrying in %.1fs",
                    attempt,
                    attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= 2
            else:
                if attempt > 1:
                    logger.info(
                        "Academy exchange send succeeded on attempt %d/%d",
                        attempt,
                        attempts,
                    )
                return

    transport.send = send_with_retry

class RemoteCallTimeoutError(TimeoutError):
    """One Academy call outlived its bound and was abandoned.

    Academy waits on a response message with no deadline of its own, so a
    response that is never delivered blocks the caller forever. Every
    delivery failure this has produced in practice -- a wedged user endpoint,
    a worker restarted mid-call, a send the hosted exchange dropped -- is
    permanent for that call, so waiting longer never helps. Failing the cell
    lets the remaining matrix run.
    """

    def __init__(self, op: str, resource: str, detail: str, limit_s: float) -> None:
        """Describe the abandoned call.

        Args:
            op: Operation name, matching the handle method.
            resource: Resource whose agent did not answer.
            detail: Short request summary.
            limit_s: Bound that expired.

        """
        super().__init__(
            f"{op} on {resource} got no response within {limit_s:g}s ({detail}). "
            "The resource's execution agent is unreachable or its response was lost."
        )
        self.op = op
        self.resource = resource
        self.limit_s = limit_s

class ResourceUnavailableError(RuntimeError):
    """A resource was declared dead and is no longer being called.

    Raised without contacting the resource at all. Once an execution agent has
    stopped answering, every further call to it costs a full ``call_timeout_s``
    and returns nothing: the jacobi-2d cell of 2026-08-07 spent forty minutes
    and two full-price model turns waiting out nineteen such calls, having
    already established with the first two that nobody was listening. Failing
    instantly turns an unbounded cost into a bounded one.
    """

    def __init__(self, resource: str, detail: str) -> None:
        """Describe the dead resource.

        Args:
            resource: Resource whose execution agent stopped answering.
            detail: Why it was declared dead, for the log and the run record.

        """
        super().__init__(
            f"resource {resource!r} is not answering and was taken out of service ({detail}). "
            "Its execution agent is wedged or gone; restart the endpoint's worker."
        )
        self.resource = resource
        self.detail = detail

async def _warn_while_pending(description: str, interval_s: float) -> None:
    """Warn once per interval for as long as a remote call stays unanswered.

    Cancelled by :meth:`AcademyExecutionBackend._traced` as soon as the call
    returns, so a healthy call logs nothing here.

    Args:
        description: Preformatted "op resource [id] detail" call description.
        interval_s: Seconds between successive warnings.

    """
    waited = 0.0
    while True:
        await asyncio.sleep(interval_s)
        waited += interval_s
        logger.warning("remote call %s unanswered after %.0fs", description, waited)

class AcademyExecutionBackend(ExecutionBackend):
    """Forward every operation to a remote ``ExecutionAgent`` handle.

    Every call is traced. Academy resolves an action by waiting on a response
    message with no deadline of its own, so a response that is never delivered
    -- a wedged user endpoint, a restarted worker, a send the exchange dropped
    -- blocks the caller silently and forever. Untraced, that surfaces only as
    a log that stops mid-run with no indication of which resource was asked for
    what. The periodic warning names the stalled call while it is still stuck,
    which is the difference between reading a stack dump and reading the log.

    Every call is also bounded, so an undelivered response fails one cell
    instead of the run. The bound covers the round trip only: an
    :class:`~lassi_x.protocol.ExecRequest` carries its own ``timeout_s`` that
    the remote worker enforces on the subprocess, so ``execute`` is allowed
    that long plus the transport margin. A response later than that is not a
    slow benchmark, it is a lost message.

    Bounding each call individually is not enough on its own, because the
    number of calls is not bounded. After ``dead_after_timeouts`` consecutive
    abandoned calls the backend takes the resource out of service and fails
    every later call immediately, so a wedged agent costs two timeouts rather
    than one per remaining call for the rest of the run.
    """

    def __init__(
        self,
        handle: Handle[ExecutionAgent],
        resource: str = "?",
        *,
        call_timeout_s: float = CALL_TIMEOUT_S,
        stall_warn_interval_s: float = STALL_WARN_INTERVAL_S,
        dead_after_timeouts: int = DEAD_AFTER_TIMEOUTS,
        on_dead: Callable[[str, str], None] | None = None,
        heartbeat_interval_s: float = HEARTBEAT_INTERVAL_S,
        heartbeat_misses: int = HEARTBEAT_MISSES,
        pause_max_s: float = PAUSE_MAX_S,
    ) -> None:
        """Configure the backend.

        Args:
            handle: Academy handle of a launched execution agent.
            resource: Resource name the handle serves, used in log lines.
            call_timeout_s: Round-trip ceiling for one call, added to an
                execute request's own remote timeout.
            stall_warn_interval_s: Seconds between warnings while a call is
                outstanding.
            dead_after_timeouts: Consecutive abandoned calls that take the
                resource out of service; ``0`` never does.
            on_dead: Called once with ``(resource, detail)`` at the moment the
                resource is taken out of service, so the run can abort rather
                than continue against a backend that cannot answer.
            heartbeat_interval_s: Seconds between liveness pings; ``0`` disables
                the heartbeat entirely.
            heartbeat_misses: Consecutive unanswered pings that pause work.
            pause_max_s: How long work may stay paused before the resource is
                retired instead of waited on.

        """
        self.handle = handle
        self.resource = resource
        self.call_timeout_s = call_timeout_s
        self.stall_warn_interval_s = stall_warn_interval_s
        self.dead_after_timeouts = dead_after_timeouts
        self.on_dead = on_dead
        self.heartbeat_interval_s = heartbeat_interval_s
        self.heartbeat_misses = heartbeat_misses
        self.pause_max_s = pause_max_s
        self._consecutive_timeouts = 0
        self._dead_detail: str | None = None
        self._live = asyncio.Event()
        self._live.set()
        self._heartbeat: asyncio.Task[None] | None = None

    @property
    def dead_detail(self) -> str | None:
        """Why this resource was taken out of service, or ``None`` if in service."""
        return self._dead_detail

    @staticmethod
    def _discard(call: Awaitable[Any]) -> None:
        """Close a handle coroutine that will never be awaited.

        Args:
            call: The unawaited handle coroutine.

        """
        close = getattr(call, "close", None)
        if callable(close):
            close()

    def _record_timeout(self, description: str) -> None:
        """Count one abandoned call and retire the resource once they repeat.

        Args:
            description: Preformatted call description, for the retirement log.

        """
        self._consecutive_timeouts += 1
        if not self.dead_after_timeouts or self._dead_detail is not None:
            return
        if self._consecutive_timeouts < self.dead_after_timeouts:
            return
        self._dead_detail = (
            f"{self._consecutive_timeouts} consecutive calls abandoned, most recently {description}"
        )
        logger.error(
            "resource %s taken out of service after %d consecutive abandoned calls; "
            "every further call to it fails immediately",
            self.resource,
            self._consecutive_timeouts,
        )
        if self.on_dead is not None:
            self.on_dead(self.resource, self._dead_detail)

    @property
    def paused(self) -> bool:
        """Whether work on this resource is currently held back."""
        return not self._live.is_set()

    async def ping(self) -> None:
        """Ask the agent to answer Academy's own ping, bounded tightly.

        This is deliberately the built-in and not an action of our own.
        ``Handle.ping`` is answered by the agent runtime rather than by user
        code, so it needs nothing deployed on the remote side and measures the
        one thing worth measuring: whether a message still reaches the agent's
        mailbox and a response still comes back. ``handshake`` was the obvious
        alternative and is the wrong tool -- it imports torch and probes every
        accelerator, far too expensive to repeat on a five-second timer.
        """
        await asyncio.wait_for(self.handle.ping(), HEARTBEAT_TIMEOUT_S)

    async def start_keepalive(self) -> None:
        """Start pinging the agent on a timer."""
        if self.heartbeat_interval_s <= 0 or self._heartbeat is not None:
            return
        self._heartbeat = asyncio.ensure_future(self._heartbeat_loop())

    async def stop_keepalive(self) -> None:
        """Stop the timer and wait for the probe task to unwind."""
        task, self._heartbeat = self._heartbeat, None
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task

    async def _heartbeat_loop(self) -> None:
        """Ping on a timer, pausing work once the pings stop being answered.

        Pausing rather than failing is the point. A real call that hits its
        bound has already spent that bound, and whatever agent turn issued it
        has already been paid for. A missed ping costs four seconds and lets
        the pipeline stop *before* it commits anything -- so the run holds
        still while somebody restarts the worker, instead of burning cells
        against a resource that stopped answering ten seconds ago.
        """
        misses = 0
        while True:
            await asyncio.sleep(self.heartbeat_interval_s)
            if self._dead_detail is not None:
                return
            try:
                await self.ping()
            except asyncio.CancelledError:
                raise
            except BaseException as exc:  # noqa: BLE001 -- any failure is a miss
                misses += 1
                logger.warning(
                    "heartbeat to %s missed (%d/%d): %s: %s",
                    self.resource,
                    misses,
                    self.heartbeat_misses,
                    type(exc).__name__,
                    exc,
                )
                if misses >= self.heartbeat_misses and self._live.is_set():
                    self._live.clear()
                    logger.error(
                        "resource %s stopped answering after %d missed heartbeats; "
                        "work is paused -- restart its endpoint worker to resume "
                        "(giving up in %.0fs)",
                        self.resource,
                        misses,
                        self.pause_max_s,
                    )
            else:
                if not self._live.is_set():
                    logger.info(
                        "resource %s is answering again after %d missed heartbeats; resuming",
                        self.resource,
                        misses,
                    )
                    self._live.set()
                misses = 0

    async def _await_resume(self, description: str) -> None:
        """Hold one call until the resource answers again, or retire it.

        Args:
            description: Preformatted call description, for the log lines.

        Raises:
            ResourceUnavailableError: The pause outlasted ``pause_max_s``.

        """
        logger.warning("remote call %s held: resource %s is paused", description, self.resource)
        try:
            await asyncio.wait_for(self._live.wait(), self.pause_max_s)
        except TimeoutError:
            detail = f"paused for {self.pause_max_s:.0f}s without answering a heartbeat"
            if self._dead_detail is None:
                self._dead_detail = detail
                logger.error("resource %s taken out of service: %s", self.resource, detail)
                if self.on_dead is not None:
                    self.on_dead(self.resource, detail)
            raise ResourceUnavailableError(self.resource, self._dead_detail or detail) from None
        logger.info("remote call %s released: resource %s resumed", description, self.resource)

    async def _traced(
        self,
        op: str,
        detail: str,
        call: Awaitable[ResultT],
        *,
        timeout_s: float | None = None,
    ) -> ResultT:
        """Await one bounded remote call, logging its start, end, and any stall.

        Args:
            op: Operation name, matching the handle method.
            detail: Short request summary, already truncated for logging.
            call: The unawaited handle coroutine.
            timeout_s: Round-trip ceiling; ``call_timeout_s`` when omitted.

        Returns:
            Whatever the remote call returned.

        Raises:
            RemoteCallTimeoutError: No response arrived before the ceiling.
            ResourceUnavailableError: The resource is already out of service.

        """
        if self._dead_detail is not None:
            self._discard(call)
            raise ResourceUnavailableError(self.resource, self._dead_detail)
        limit = self.call_timeout_s if timeout_s is None else timeout_s
        description = f"{op} on {self.resource} [{uuid.uuid4().hex[:8]}] {detail}"
        if self.paused:
            # Held before the request is sent, so a paused resource costs the
            # wait and nothing else -- no bound consumed, no response to lose.
            try:
                await self._await_resume(description)
            except BaseException:
                self._discard(call)
                raise
        logger.info("remote call %s started (bound %.0fs)", description, limit)
        watchdog = asyncio.ensure_future(
            _warn_while_pending(description, self.stall_warn_interval_s)
        )
        started = time.monotonic()
        try:
            result = await asyncio.wait_for(call, limit)
        except TimeoutError:
            logger.error("remote call %s abandoned after %.0fs", description, limit)
            self._record_timeout(description)
            raise RemoteCallTimeoutError(op, self.resource, detail, limit) from None
        except BaseException as exc:
            logger.warning(
                "remote call %s failed after %.1fs: %s: %s",
                description,
                time.monotonic() - started,
                type(exc).__name__,
                exc,
            )
            raise
        else:
            # Only a completed round trip proves the agent is still there, so
            # this is the one place the timeout streak may be cleared.
            self._consecutive_timeouts = 0
            logger.info("remote call %s finished in %.1fs", description, time.monotonic() - started)
            return result
        finally:
            watchdog.cancel()

    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined remote workspace."""
        argv = " ".join(request.argv)
        if len(argv) > _ARGV_LOG_LIMIT:
            argv = f"{argv[:_ARGV_LOG_LIMIT]}..."
        detail = f"{request.workspace}: {argv} (timeout {request.timeout_s:.0f}s)"
        return await self._traced(
            "execute",
            detail,
            self.handle.execute(request),
            timeout_s=request.timeout_s + self.call_timeout_s,
        )

    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined remote workspace."""
        detail = f"{request.workspace}:{request.path}"
        return await self._traced("put_file", detail, self.handle.put_file(request))

    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined remote workspace."""
        detail = f"{request.workspace}:{request.path} at offset {request.offset}"
        return await self._traced("get_file", detail, self.handle.get_file(request))

    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined remote workspace."""
        detail = f"{request.workspace}:{request.path}"
        return await self._traced("list_dir", detail, self.handle.list_dir(request))

    async def handshake(self) -> HandshakeReport:
        """Measure and report the remote host's capabilities."""
        return await self._traced("handshake", "capability probe", self.handle.handshake())

def _resource_executor(name: str, spec: ResourceConfig) -> Executor:
    """Build the executor that launches one resource's execution agent.

    Args:
        name: Resource name, used in error messages.
        spec: Resource configuration.

    Returns:
        A Globus Compute executor for endpoint resources, otherwise a local
        thread pool.

    Raises:
        RuntimeError: If an endpoint is configured but ``globus-compute-sdk``
            is not installed.

    """
    if spec.endpoint_id is None:
        return ThreadPoolExecutor(max_workers=4)
    try:
        from globus_compute_sdk import Executor as GlobusComputeExecutor  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            f"resource {name!r} names Globus Compute endpoint {spec.endpoint_id} "
            "but globus-compute-sdk is not installed; install lassi-x[globus]"
        ) from exc
    # Assigned to a typed name so mypy accepts this whether or not the
    # optional globus-compute-sdk (untyped when absent) is installed.
    executor: Executor = GlobusComputeExecutor(spec.endpoint_id)
    return executor
