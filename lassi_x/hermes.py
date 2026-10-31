from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import random
import shutil
import signal
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from .protocol import (
    MAX_FRAME_BYTES,
    MemorySettings,
    WireModel,
    WorkerClose,
    WorkerFailure,
    WorkerInit,
    WorkerReady,
    WorkerResponse,
    WorkerSend,
    WorkerTurn,
    parse_worker_response,
)
from .types import Usage

if TYPE_CHECKING:
    from .config import MemoryConfig, ModelConfig

logger = logging.getLogger(__name__)
WORKER_SHUTDOWN_GRACE_S = 5.0


@dataclass(slots=True)
class HermesTurn:
    """Normalized result from one Hermes conversation turn.

    Attributes:
        text: Final textual response produced by the agent.
        usage: Token and estimated-cost delta attributed to this turn.
        completed: Whether Hermes reported a normal completed turn.
        exit_reason: Hermes diagnostic explaining why the turn stopped.
        attempts: Number of outer agent-layer attempts used for this turn.

    """

    text: str
    usage: Usage
    completed: bool = True
    exit_reason: str = "unknown"
    attempts: int = 1


class HermesSession:
    """Manage one persistent Hermes worker process and conversation."""

    def __init__(
        self,
        model: ModelConfig,
        *,
        cwd: Path,
        system_prompt: str,
        toolsets: list[str],
        role: str,
        memory: MemoryConfig | None = None,
        hermes_home: Path | None = None,
    ) -> None:
        """Configure a lazy persistent agent session.

        Args:
            model: Hermes model, provider, credential, and turn-limit configuration.
            cwd: Isolated working directory exposed to the agent tools.
            system_prompt: Stable role and behavioral instructions for the agent.
            toolsets: Hermes toolset names enabled for the session.
            role: Human-readable role identifier used for auditability.
            memory: Mem0 memory settings; the session stays memoryless when
                ``None`` or disabled. The role becomes the Mem0 agent
                identifier so stored facts are attributable per agent.

        """
        self.model = model
        self.cwd = cwd
        self.system_prompt = system_prompt
        self.toolsets = toolsets
        self.role = role
        self.memory = memory
        self.hermes_home = hermes_home
        self._profile: tempfile.TemporaryDirectory[str] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._stderr_tail = bytearray()
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> None:
        """Start and initialize the worker process if it is not already running.

        The worker is launched with the package source on ``PYTHONPATH`` and receives one
        :class:`~lassi_x.protocol.WorkerInit` message containing model, credential-source,
        prompt, and toolset configuration.

        Raises:
            OSError: If the Python worker process cannot be created.
            RuntimeError: If the worker rejects initialization or exits unexpectedly.
            pydantic.ValidationError: If the worker returns malformed protocol data.

        """
        if self._process is not None:
            return
        from .skills import hermes_home as resolve_home  # noqa: PLC0415
        from .skills import install_skills  # noqa: PLC0415

        try:
            env = os.environ.copy()
            self._profile = tempfile.TemporaryDirectory(prefix="lassi-hermes-")
            profile = Path(self._profile.name)
            source_home = resolve_home(self.hermes_home)
            for name in ("config.yaml", ".env", "auth.json"):
                source = source_home / name
                if name != "config.yaml" and not source.is_file():
                    source = resolve_home() / name
                if source.is_file():
                    shutil.copy2(source, profile / name)
            # Plugins can contain provider implementations; share their code, not state.
            plugins = source_home / "plugins"
            if plugins.is_dir():
                (profile / "plugins").symlink_to(plugins, target_is_directory=True)
            install_skills(profile)
            env["HERMES_HOME"] = str(profile)
            self._stderr_tail.clear()
            package_root = str(Path(__file__).resolve().parents[1])
            env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")
            async with asyncio.timeout(self.model.turn_timeout_s):
                self._process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "lassi_x.hermes_worker",
                    cwd=self.cwd,
                    env=env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                    limit=MAX_FRAME_BYTES,
                )
                assert self._process.stderr is not None
                self._stderr_task = asyncio.create_task(self._drain_stderr(self._process.stderr))
                await self._write(
                    WorkerInit(
                        model=self.model.model,
                        provider=self.model.provider,
                        base_url=self.model.base_url,
                        providers_allowed=self.model.providers_allowed,
                        api_mode=self.model.api_mode,
                        reasoning_effort=self.model.reasoning_effort,
                        api_key_env=self.model.api_key_env,
                        claude_settings=(
                            str(self.model.claude_settings.expanduser())
                            if self.model.claude_settings
                            else None
                        ),
                        max_iterations=self.model.max_iterations,
                        max_tokens=self.model.max_tokens,
                        system_prompt=self.system_prompt,
                        toolsets=self.toolsets,
                        role=self.role,
                        memory=self._memory_settings(),
                    )
                )
                response = await self._read()
                if isinstance(response, WorkerFailure):
                    raise RuntimeError(response.error)
                if not isinstance(response, WorkerReady):
                    raise RuntimeError(
                        f"unexpected worker initialization response: {response.kind}"
                    )
        except BaseException:
            await self.close()
            raise

    async def _drain_stderr(self, stream: asyncio.StreamReader) -> None:
        """Continuously drain diagnostics while retaining a bounded byte tail."""
        while chunk := await stream.read(8192):
            self._stderr_tail.extend(chunk)
            del self._stderr_tail[:-4000]

    def _memory_settings(self) -> MemorySettings | None:
        """Build the wire memory settings for this session's role.

        Returns:
            Settings carrying the session role as the Mem0 agent identifier,
            or ``None`` when run memory is absent or disabled.

        """
        if self.memory is None or not self.memory.enabled:
            return None
        return MemorySettings(
            host=self.memory.host,
            api_key_env=self.memory.api_key_env,
            user_id=self.memory.user_id,
            agent_id=self.role,
        )

    async def send(self, prompt: str) -> HermesTurn:
        """Send one user prompt through the persistent agent conversation.

        Args:
            prompt: Task or correction message for the configured agent role.

        Returns:
            Normalized response text and per-turn usage delta.

        Raises:
            RuntimeError: If the worker rejects the turn or terminates unexpectedly.
            pydantic.ValidationError: If the worker returns malformed protocol data.

        """
        response: WorkerTurn | None = None
        last_error: Exception | None = None
        retry_usage = Usage()
        started = time.monotonic()
        # The model layer was the one part of a run that logged nothing, so a
        # turn that took twenty minutes and a turn that hung looked identical
        # from outside. Announce the turn before it blocks, not after.
        logger.info(
            "turn start role=%s model=%s prompt_chars=%d timeout=%.0fs",
            self.role,
            self.model.model,
            len(prompt),
            self.model.turn_timeout_s,
        )
        for attempt in range(self.model.turn_retries + 1):
            try:
                async with asyncio.timeout(self.model.turn_timeout_s):
                    await self.start()
                    await self._write(WorkerSend(prompt=prompt))
                    raw_response = await self._read()
                if isinstance(raw_response, WorkerFailure):
                    retry_usage.add(
                        Usage(
                            input_tokens=raw_response.usage.input_tokens,
                            output_tokens=raw_response.usage.output_tokens,
                            estimated_cost_usd=raw_response.usage.estimated_cost_usd,
                        )
                    )
                    raise RuntimeError(raw_response.error)
                if not isinstance(raw_response, WorkerTurn):
                    raise RuntimeError(f"unexpected worker turn response: {raw_response.kind}")
                response = raw_response
                break
            except asyncio.CancelledError:
                await self.close()
                raise
            except (
                BrokenPipeError,
                ConnectionError,
                OSError,
                RuntimeError,
                ValidationError,
            ) as exc:
                last_error = exc
                if (
                    isinstance(exc, (TimeoutError, ValidationError, BrokenPipeError))
                    or "protocol frame" in str(exc)
                    or self._process is None
                    or self._process.returncode is not None
                ):
                    await self.close()
                if attempt >= self.model.turn_retries or not self._retryable(exc):
                    # This is the raise that ended fifteen runs while the log's
                    # last line was an unrelated stage start. Name the cause here,
                    # where it happens, rather than leaving it to run.json.
                    logger.error(
                        "turn failed role=%s model=%s attempt=%d/%d after %.1fs "
                        "retryable=%s error=%s: %s",
                        self.role,
                        self.model.model,
                        attempt + 1,
                        self.model.turn_retries + 1,
                        time.monotonic() - started,
                        self._retryable(exc),
                        type(exc).__name__,
                        exc,
                    )
                    raise
                delay = min(
                    self.model.retry_initial_s * (2**attempt),
                    self.model.retry_max_s,
                )
                delay += random.uniform(0.0, self.model.retry_jitter_s)
                logger.warning(
                    "turn retry role=%s model=%s attempt=%d/%d in %.1fs error=%s: %s",
                    self.role,
                    self.model.model,
                    attempt + 1,
                    self.model.turn_retries + 1,
                    delay,
                    type(exc).__name__,
                    exc,
                )
                await asyncio.sleep(delay)
        if response is None:
            logger.error(
                "turn failed role=%s model=%s after %.1fs with no response: %s",
                self.role,
                self.model.model,
                time.monotonic() - started,
                last_error,
            )
            raise RuntimeError("Hermes turn failed without a response") from last_error
        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            estimated_cost_usd=response.usage.estimated_cost_usd,
        )
        usage.add(retry_usage)
        # Cost and token counts were computed here and shown to nobody until the
        # run finished, so a runaway turn could not be spotted while it ran.
        logger.info(
            "turn finish role=%s model=%s in %.1fs attempts=%d tokens_in=%d "
            "tokens_out=%d cost_usd=%.4f completed=%s exit_reason=%s reply_chars=%d",
            self.role,
            self.model.model,
            time.monotonic() - started,
            attempt + 1,
            usage.input_tokens,
            usage.output_tokens,
            usage.estimated_cost_usd,
            response.completed,
            response.exit_reason,
            len(response.text),
        )
        return HermesTurn(
            text=response.text,
            usage=usage,
            completed=response.completed,
            exit_reason=response.exit_reason,
            attempts=attempt + 1,
        )

    @staticmethod
    def _retryable(exc: Exception) -> bool:
        """Return whether an agent-layer failure may be transient.

        Credential and configuration failures are deterministic. Provider, transport,
        rate-limit, timeout, worker-exit, and malformed-protocol failures receive bounded
        exponential backoff.

        Args:
            exc: Exception raised while starting or communicating with a worker.

        Returns:
            ``True`` when retrying the same turn is appropriate.

        """
        message = str(exc).lower()
        deterministic = (
            "credential environment variable",
            "apikeyhelper",
            "unknown worker operation",
            "cannot load",
            # A turn whose tool calls were waiting on a retired resource is not
            # transient, and it is the most expensive thing here to retry: the
            # jacobi-2d cell paid twice for two turns of roughly 1900s each,
            # both of which were only ever going to time out again.
            "was taken out of service",
        )
        return not any(marker in message for marker in deterministic)

    async def close(self) -> None:
        """Close the worker gracefully, terminating it if shutdown stalls.

        Calling this method more than once is safe. The process reference is cleared
        before shutdown so the session cannot accidentally reuse a closing worker.

        """
        process, self._process = self._process, None
        stdout_task = (
            asyncio.create_task(self._discard_stdout(process.stdout))
            if process is not None and process.stdout is not None
            else None
        )
        try:
            if process is not None and process.returncode is None:
                try:
                    async with asyncio.timeout(WORKER_SHUTDOWN_GRACE_S):
                        await self._write_to(process, WorkerClose())
                        await process.wait()
                except (OSError, RuntimeError):
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGTERM)
                    try:
                        await asyncio.wait_for(process.wait(), timeout=WORKER_SHUTDOWN_GRACE_S)
                    except TimeoutError:
                        with contextlib.suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                        await process.wait()
        finally:
            if stdout_task is not None:
                stdout_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await stdout_task
            if self._stderr_task is not None:
                self._stderr_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._stderr_task
                self._stderr_task = None
            if self._profile is not None:
                self._profile.cleanup()
                self._profile = None

    @staticmethod
    async def _discard_stdout(stream: asyncio.StreamReader) -> None:
        """Allow an exiting worker to flush output without retaining it."""
        while await stream.read(8192):
            pass

    async def _write(self, message: WireModel) -> None:
        """Write a protocol message to the active worker.

        Args:
            message: Validated worker request message.

        Raises:
            RuntimeError: If the session has no active worker process.

        """
        if self._process is None:
            raise RuntimeError("Hermes worker is not running")
        await self._write_to(self._process, message)

    @staticmethod
    async def _write_to(process: asyncio.subprocess.Process, message: WireModel) -> None:
        """Serialize one JSONL request to a specific worker process.

        Args:
            process: Worker process whose standard input receives the request.
            message: Validated worker request message.

        Raises:
            RuntimeError: If the worker standard-input pipe is unavailable.

        """
        if process.stdin is None:
            raise RuntimeError("Hermes worker stdin is unavailable")
        process.stdin.write((message.model_dump_json() + "\n").encode())
        await process.stdin.drain()

    async def _read(self) -> WorkerResponse:
        """Read and validate one JSONL response from the active worker.

        Returns:
            Validated worker response message.

        Raises:
            RuntimeError: If no readable worker exists or the worker exits early.
            pydantic.ValidationError: If the response line is not a valid message.

        """
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("Hermes worker stdout is unavailable")
        try:
            line = await self._process.stdout.readline()
        except ValueError as exc:
            raise RuntimeError("worker protocol frame exceeds byte limit") from exc
        if not line:
            stderr = self._stderr_tail.decode(errors="replace")
            raise RuntimeError(f"Hermes worker exited unexpectedly: {stderr}")
        return parse_worker_response(line)

    async def __aenter__(self) -> HermesSession:
        """Start the worker and enter the asynchronous session context.

        Returns:
            The initialized session.

        """
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close the worker when leaving the asynchronous session context.

        Args:
            *_: Optional exception context supplied by the asynchronous context manager.

        """
        await self.close()
