"""Execution backends: one interface for local and Academy-remote work.

The harness and the MCP tool server both talk to an :class:`ExecutionBackend`.
:class:`LocalExecutionBackend` runs everything in-process against a local
directory, while :class:`AcademyExecutionBackend` forwards each call to an
:class:`~lassi_x.remote.agent.ExecutionAgent` handle living on an HPC
resource. Both share the operation semantics in :mod:`lassi_x.remote.ops`, so
switching a run between local and remote execution changes transport only.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, TypeVar

from .protocol import MAX_INLINE_BYTES, ExecRequest, FileGet, FilePut
from .remote import ops

logger = logging.getLogger(__name__)

TRANSFER_CHUNK_BYTES = 128 * 1024
"""Conservative raw chunk size for Academy exchange messages."""

_ASSEMBLE_CHUNKS = """\
import hashlib
import os
from pathlib import Path
import sys

destination = Path(sys.argv[1])
temporary = Path(sys.argv[2])
expected_digest = sys.argv[3]
parts = [Path(value) for value in sys.argv[4:]]
destination.parent.mkdir(parents=True, exist_ok=True)
digest = hashlib.sha256()
with temporary.open("wb") as output:
    for part in parts:
        data = part.read_bytes()
        digest.update(data)
        output.write(data)
if digest.hexdigest() != expected_digest:
    temporary.unlink(missing_ok=True)
    raise RuntimeError("assembled file digest mismatch")
os.replace(temporary, destination)
for part in parts:
    part.unlink()
parts[0].parent.rmdir()
"""


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


SEND_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
"""Hosted-exchange responses worth retrying: gateway, overload, and timeout."""

SEND_RETRY_ATTEMPTS = 5
"""Total send attempts, including the first."""

SEND_RETRY_BASE_DELAY_S = 0.5
"""First backoff pause; doubled after each failed attempt."""


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


if TYPE_CHECKING:
    from collections.abc import Awaitable
    from concurrent.futures import Executor
    from pathlib import Path

    from academy.handle import Handle

    from .config import ResourceConfig, RunConfig
    from .protocol import (
        DirListing,
        ExecResult,
        FileContent,
        FileStat,
        HandshakeReport,
        ListDir,
    )
    from .remote.agent import ExecutionAgent


class ExecutionBackend(ABC):
    """Workspace-confined execution and file operations on one resource."""

    _cached_handshake: HandshakeReport | None = None

    @abstractmethod
    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined workspace."""

    @abstractmethod
    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined workspace."""

    @abstractmethod
    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined workspace."""

    @abstractmethod
    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined workspace."""

    @abstractmethod
    async def handshake(self) -> HandshakeReport:
        """Measure and report the executing host's capabilities."""

    async def cached_handshake(self) -> HandshakeReport:
        """Return the handshake, measuring it at most once per backend.

        Returns:
            The measured or previously cached handshake report.

        """
        if self._cached_handshake is None:
            self._cached_handshake = await self.handshake()
        return self._cached_handshake


async def fetch_bytes(
    backend: ExecutionBackend,
    workspace: str,
    path: str,
    *,
    chunk_size: int | None = None,
) -> bytes:
    """Fetch one workspace file of any size through chunked reads.

    Args:
        backend: Backend serving the workspace.
        workspace: Workspace identifier.
        path: Workspace-relative file path.
        chunk_size: Maximum bytes per read; defaults to the inline limit.

    Returns:
        The complete file content.

    Raises:
        ValueError: If the path escapes the workspace.
        OSError: If the file cannot be read on the executing side.

    """
    chunks: list[bytes] = []
    offset = 0
    while True:
        content = await backend.get_file(
            FileGet(
                workspace=workspace,
                path=path,
                offset=offset,
                max_bytes=chunk_size or MAX_INLINE_BYTES,
            )
        )
        data = (
            base64.b64decode(content.content)
            if content.encoding == "base64"
            else content.content.encode()
        )
        chunks.append(data)
        offset += len(data)
        if not content.truncated:
            return b"".join(chunks)


async def put_bytes(
    backend: ExecutionBackend,
    workspace: str,
    path: str,
    data: bytes,
    *,
    chunk_size: int = TRANSFER_CHUNK_BYTES,
) -> None:
    """Stage bytes through bounded messages and atomically assemble large files.

    Args:
        backend: Backend serving the destination workspace.
        workspace: Workspace identifier.
        path: Workspace-relative destination path.
        data: Complete file payload.
        chunk_size: Maximum raw bytes carried by one message.

    Raises:
        ValueError: If ``path`` is unsafe or ``chunk_size`` is not positive.
        OSError: If remote chunk assembly or integrity verification fails.

    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    # Validate the final path with the wire model even when it will only be
    # written by the assembly command.
    FilePut(workspace=workspace, path=path, content_b64="")
    digest = hashlib.sha256(data).hexdigest()
    if len(data) <= chunk_size:
        await backend.put_file(
            FilePut(
                workspace=workspace,
                path=path,
                content_b64=base64.b64encode(data).decode(),
                sha256=digest,
            )
        )
        return

    transfer_id = uuid.uuid4().hex
    part_dir = f".lassi-transfer-{transfer_id}"
    part_paths: list[str] = []
    for index, offset in enumerate(range(0, len(data), chunk_size)):
        chunk = data[offset : offset + chunk_size]
        part_path = f"{part_dir}/{index:08d}.part"
        part_paths.append(part_path)
        await backend.put_file(
            FilePut(
                workspace=workspace,
                path=part_path,
                content_b64=base64.b64encode(chunk).decode(),
                sha256=hashlib.sha256(chunk).hexdigest(),
            )
        )
    temporary = f"{part_dir}/assembled.tmp"
    handshake = await backend.cached_handshake()
    result = await backend.execute(
        ExecRequest(
            workspace=workspace,
            argv=[
                handshake.python_executable,
                "-c",
                _ASSEMBLE_CHUNKS,
                path,
                temporary,
                digest,
                *part_paths,
            ],
            timeout_s=600,
        )
    )
    if not result.ok:
        raise OSError(
            f"failed to assemble staged file {path!r}: {(result.stderr or result.stdout)[-2000:]}"
        )


class LocalExecutionBackend(ExecutionBackend):
    """Run every operation in-process against a local workspace root."""

    def __init__(self, workspace_root: Path, resource: str | None = None) -> None:
        """Configure the backend.

        Args:
            workspace_root: Directory beneath which all workspaces live.
            resource: Resource name reported in the handshake.

        """
        self.workspace_root = workspace_root
        self.resource = resource

    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined workspace."""
        return await ops.run_exec(self.workspace_root, request)

    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined workspace."""
        return ops.put_file(self.workspace_root, request)

    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined workspace."""
        return ops.get_file(self.workspace_root, request)

    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined workspace."""
        return ops.list_dir(self.workspace_root, request)

    async def handshake(self) -> HandshakeReport:
        """Measure and report this host's capabilities."""
        return await ops.build_handshake(self.workspace_root, self.resource)


STALL_WARN_INTERVAL_S = 60.0
"""Seconds between "still waiting" warnings for one unanswered remote call."""

CALL_TIMEOUT_S = 300.0
"""Default ceiling for one Academy round trip, excluding remote run time."""


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


_ARGV_LOG_LIMIT = 160
"""Characters of a command line kept in the call log line."""

ResultT = TypeVar("ResultT")
"""Whatever one traced remote call resolves to."""


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
    """

    def __init__(
        self,
        handle: Handle[ExecutionAgent],
        resource: str = "?",
        *,
        call_timeout_s: float = CALL_TIMEOUT_S,
        stall_warn_interval_s: float = STALL_WARN_INTERVAL_S,
    ) -> None:
        """Configure the backend.

        Args:
            handle: Academy handle of a launched execution agent.
            resource: Resource name the handle serves, used in log lines.
            call_timeout_s: Round-trip ceiling for one call, added to an
                execute request's own remote timeout.
            stall_warn_interval_s: Seconds between warnings while a call is
                outstanding.

        """
        self.handle = handle
        self.resource = resource
        self.call_timeout_s = call_timeout_s
        self.stall_warn_interval_s = stall_warn_interval_s

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

        """
        limit = self.call_timeout_s if timeout_s is None else timeout_s
        description = f"{op} on {self.resource} [{uuid.uuid4().hex[:8]}] {detail}"
        logger.info("remote call %s started (bound %.0fs)", description, limit)
        watchdog = asyncio.ensure_future(
            _warn_while_pending(description, self.stall_warn_interval_s)
        )
        started = time.monotonic()
        try:
            result = await asyncio.wait_for(call, limit)
        except TimeoutError:
            logger.error("remote call %s abandoned after %.0fs", description, limit)
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


class ExecutionContext:
    """Everything one run needs to fan tool calls out to its resources.

    Owns the execution backends (in-process or Academy-launched), the local
    MCP server the Hermes sessions connect to, and the per-workspace server
    entries registered in the Hermes configuration. Create it with
    :meth:`start` and always close it (or use ``async with``) so Hermes
    configuration entries and background services are cleaned up.
    """

    def __init__(
        self,
        *,
        backends: dict[str, ExecutionBackend],
        default_resource: str,
        mirror_root: Path,
        mcp_timeout_s: float,
        hermes_home: Path | None = None,
        enable_memory: bool = False,
    ) -> None:
        """Wire the context; use :meth:`start` instead of calling this directly.

        Args:
            backends: Execution backends keyed by resource name.
            default_resource: Resource used when a request names none.
            mirror_root: Harness-local directory holding the mirrored copy of
                every workspace's artifacts of record.
            mcp_timeout_s: Per-tool-call timeout written into Hermes entries.
            hermes_home: Hermes home override for configuration registration.
            enable_memory: Whether to activate the Mem0 memory provider in the
                Hermes configuration for the duration of the run.

        """
        from .mcp_server import LassiMCPServer, MCPServerRunner  # noqa: PLC0415

        self.backends = backends
        self.default_resource = default_resource
        self.mirror_root = mirror_root
        self.mcp_timeout_s = mcp_timeout_s
        self.hermes_home = hermes_home
        self.enable_memory = enable_memory
        self.mcp = LassiMCPServer(backends, default_resource=default_resource)
        self.runner = MCPServerRunner(self.mcp)
        self.registered_servers: list[str] = []
        self._manager: object | None = None
        self._memory_active = False
        self._memory_previous: str | None = None

    @classmethod
    async def start(
        cls,
        config: RunConfig,
        run_dir: Path,
        *,
        hermes_home: Path | None = None,
    ) -> ExecutionContext:
        """Build backends from configuration and start the MCP server.

        In ``academy`` mode one :class:`~lassi_x.remote.agent.ExecutionAgent`
        is launched per configured resource. Without an ``exchange_url`` the
        agents run through a local exchange on this machine; with one, the
        manager connects to the remote (Globus-authenticated) exchange and
        resources carrying an ``endpoint_id`` are launched onto their Globus
        Compute endpoints.

        Args:
            config: Validated run configuration.
            run_dir: Root artifact directory for the current pipeline run.
            hermes_home: Hermes home override for configuration registration.

        Returns:
            A running context ready to register workspaces.

        Raises:
            RuntimeError: If an endpoint resource is configured but the
                ``globus-compute-sdk`` optional dependency is not installed.

        """
        from .config import ResourceConfig  # noqa: PLC0415

        execution = config.execution
        resources = execution.resources or {"local": ResourceConfig()}
        default_resource = execution.default_resource or next(iter(resources))
        mirror_root = run_dir / "workspaces"
        backends: dict[str, ExecutionBackend] = {}
        manager: object | None = None
        if execution.mode == "local":
            backends = {
                name: LocalExecutionBackend(spec.workspace_root or mirror_root, name)
                for name, spec in resources.items()
            }
        else:
            from academy.exchange import LocalExchangeFactory  # noqa: PLC0415
            from academy.handle import Handle  # noqa: PLC0415
            from academy.manager import Manager  # noqa: PLC0415

            from .remote.agent import ExecutionAgent  # noqa: PLC0415

            executors: dict[str, Executor | None] = {
                name: _resource_executor(name, spec) for name, spec in resources.items()
            }
            if execution.exchange_url is None:
                manager = await Manager.from_exchange_factory(
                    factory=LocalExchangeFactory(), executors=executors
                )
            else:
                from academy.exchange.cloud.client import HttpExchangeFactory  # noqa: PLC0415

                class PersistentHttpExchangeFactory(HttpExchangeFactory):
                    """Create hosted-exchange transports safe for long pipelines."""

                    async def _create_transport(self, *args: Any, **kwargs: Any) -> Any:
                        transport = await super()._create_transport(*args, **kwargs)
                        _disable_academy_stream_deadline(transport)
                        _add_academy_send_retry(transport)
                        return transport

                manager = await Manager.from_exchange_factory(
                    factory=PersistentHttpExchangeFactory(
                        execution.exchange_url,
                        auth_method="globus" if execution.auth == "globus" else None,
                    ),
                    executors=executors,
                )
            for name, spec in resources.items():
                agent_root = spec.workspace_root or mirror_root
                launched = await manager.launch(
                    ExecutionAgent,
                    args=(str(agent_root), name),
                    executor=name,
                )
                # Bind the exchange client explicitly: backend calls happen in
                # HTTP-handler tasks that never enter the manager context.
                handle: Handle[ExecutionAgent] = Handle(
                    launched.agent_id, exchange=manager.exchange_client
                )
                backends[name] = AcademyExecutionBackend(
                    handle, name, call_timeout_s=execution.call_timeout_s
                )
        context = cls(
            backends=backends,
            default_resource=default_resource,
            mirror_root=mirror_root,
            mcp_timeout_s=execution.mcp_timeout_s,
            hermes_home=hermes_home,
            enable_memory=config.memory.enabled,
        )
        context._manager = manager
        try:
            await context.runner.start()
            if context.enable_memory:
                from .hermes_config import enable_memory_provider  # noqa: PLC0415

                context._memory_previous = enable_memory_provider(home=context.hermes_home)
                context._memory_active = True
        except BaseException:
            await context.close()
            raise
        return context

    def workspace_dir(self, workspace: str) -> Path:
        """Locate the harness-local mirror directory of one workspace.

        In local execution this is the workspace itself; for remote resources
        it holds the mirrored artifacts of record fetched via
        :meth:`mirror_file`.

        Args:
            workspace: Workspace identifier.

        Returns:
            The local mirror directory.

        """
        return self.mirror_root / workspace

    def backend(self, resource: str | None = None) -> ExecutionBackend:
        """Resolve one execution backend.

        Args:
            resource: Resource name; default resource if omitted.

        Returns:
            The matching backend.

        """
        return self.backends[resource or self.default_resource]

    async def stage_bytes(self, workspace: str, path: str, data: bytes) -> None:
        """Write one file into a workspace on every resource.

        Staging fans out to all resources so an agent may run commands against
        the staged inputs on whichever machine it selects.

        Args:
            workspace: Workspace identifier.
            path: Workspace-relative destination path.
            data: File content.

        """
        for backend in self.backends.values():
            await put_bytes(backend, workspace, path, data)

    async def fetch_bytes(self, workspace: str, path: str, resource: str | None = None) -> bytes:
        """Fetch one workspace file from a resource, chunking large files.

        Args:
            workspace: Workspace identifier.
            path: Workspace-relative file path.
            resource: Resource to fetch from; default resource if omitted.

        Returns:
            The complete file content.

        """
        return await fetch_bytes(self.backend(resource), workspace, path)

    async def mirror_file(self, workspace: str, path: str, resource: str | None = None) -> Path:
        """Copy one workspace file into the harness-local mirror directory.

        Args:
            workspace: Workspace identifier.
            path: Workspace-relative file path.
            resource: Resource to fetch from; default resource if omitted.

        Returns:
            The local mirrored file path.

        """
        data = await self.fetch_bytes(workspace, path, resource)
        destination = self.workspace_dir(workspace) / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return destination

    def register_workspace(self, workspace: str) -> str:
        """Expose one workspace to Hermes as a header-pinned MCP toolset.

        Args:
            workspace: Workspace identifier to pin.

        Returns:
            The Hermes toolset name for the workspace.

        """
        from .hermes_config import register_workspace_servers, server_name  # noqa: PLC0415

        name = server_name(workspace)
        if name not in self.registered_servers:
            register_workspace_servers(
                self.runner.url,
                [workspace],
                home=self.hermes_home,
                timeout_s=self.mcp_timeout_s,
            )
            self.registered_servers.append(name)
        return name

    async def handshakes(self) -> dict[str, HandshakeReport]:
        """Measure (or reuse) the handshake of every resource, concurrently.

        Probing in parallel keeps one mute resource from masking the health of
        the others: sequentially, the first unanswered handshake consumed the
        whole preflight and the report named only that resource.

        Returns:
            Handshake reports keyed by resource name.

        """
        names = sorted(self.backends)
        reports = await asyncio.gather(*(self.mcp.handshake(name) for name in names))
        return dict(zip(names, reports, strict=True))

    async def close(self) -> None:
        """Remove Hermes entries and stop the MCP server and agents.

        Cleanup is best-effort: a failure while shutting remote agents down
        (for example when the exchange is unreachable) is logged and
        suppressed so it never masks the error that ended the run.
        """
        from .hermes_config import (  # noqa: PLC0415
            restore_memory_provider,
            unregister_workspace_servers,
        )

        if self.registered_servers:
            unregister_workspace_servers(self.registered_servers, home=self.hermes_home)
            self.registered_servers = []
        if self._memory_active:
            restore_memory_provider(self._memory_previous, home=self.hermes_home)
            self._memory_active = False
            self._memory_previous = None
        await self.runner.stop()
        manager = self._manager
        self._manager = None
        if manager is not None:
            from academy.handle import exchange_context  # noqa: PLC0415
            from academy.manager import Manager  # noqa: PLC0415

            assert isinstance(manager, Manager)
            # Manager.close() shuts agents down through handles that resolve
            # their exchange client from the context variable normally set by
            # ``async with manager``; set it here since the manager lives
            # outside a single task's context.
            token = exchange_context.set(manager.exchange_client)
            try:
                await manager.close()
            except Exception as exc:  # noqa: BLE001  # cleanup must not mask run errors
                logger.warning("execution manager shutdown failed: %s: %s", type(exc).__name__, exc)
            finally:
                exchange_context.reset(token)

    async def __aenter__(self) -> ExecutionContext:
        """Enter the asynchronous context.

        Returns:
            The running context.

        """
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close the context when leaving the asynchronous scope."""
        await self.close()
