from __future__ import annotations

import asyncio
import contextlib
import json
import os
import random
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from .types import Usage

if TYPE_CHECKING:
    from .config import ModelConfig


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
    ) -> None:
        """Configure a lazy persistent agent session.

        Args:
            model: Hermes model, provider, credential, and turn-limit configuration.
            cwd: Isolated working directory exposed to the agent tools.
            system_prompt: Stable role and behavioral instructions for the agent.
            toolsets: Hermes toolset names enabled for the session.
            role: Human-readable role identifier used for auditability.

        """
        self.model = model
        self.cwd = cwd
        self.system_prompt = system_prompt
        self.toolsets = toolsets
        self.role = role
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> None:
        """Start and initialize the worker process if it is not already running.

        The worker is launched with the package source on ``PYTHONPATH`` and receives one
        initialization message containing model, credential-source, prompt, and toolset
        configuration.

        Raises:
            OSError: If the Python worker process cannot be created.
            RuntimeError: If the worker rejects initialization or exits unexpectedly.
            json.JSONDecodeError: If the worker returns malformed protocol data.

        """
        if self._process is not None:
            return
        env = os.environ.copy()
        package_root = str(Path(__file__).resolve().parents[1])
        env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")
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
        )
        await self._write(
            {
                "op": "init",
                "model": self.model.model,
                "provider": self.model.provider,
                "base_url": self.model.base_url,
                "api_mode": self.model.api_mode,
                "api_key_env": self.model.api_key_env,
                "claude_settings": (
                    str(self.model.claude_settings.expanduser())
                    if self.model.claude_settings
                    else None
                ),
                "max_iterations": self.model.max_iterations,
                "max_tokens": self.model.max_tokens,
                "system_prompt": self.system_prompt,
                "toolsets": self.toolsets,
                "role": self.role,
            }
        )
        response = await self._read()
        if not response.get("ok"):
            await self.close()
            raise RuntimeError(response.get("error", "Hermes worker initialization failed"))

    async def send(self, prompt: str) -> HermesTurn:
        """Send one user prompt through the persistent agent conversation.

        Args:
            prompt: Task or correction message for the configured agent role.

        Returns:
            Normalized response text and per-turn usage delta.

        Raises:
            RuntimeError: If the worker rejects the turn or terminates unexpectedly.
            json.JSONDecodeError: If the worker returns malformed protocol data.

        """
        response: dict[str, Any] | None = None
        last_error: Exception | None = None
        retry_usage = Usage()
        for attempt in range(self.model.turn_retries + 1):
            try:
                await self.start()
                await self._write({"op": "send", "prompt": prompt})
                response = await asyncio.wait_for(self._read(), timeout=self.model.turn_timeout_s)
                if not response.get("ok"):
                    raw_failed = response.get("usage") or {}
                    retry_usage.add(
                        Usage(
                            input_tokens=int(raw_failed.get("input_tokens") or 0),
                            output_tokens=int(raw_failed.get("output_tokens") or 0),
                            estimated_cost_usd=float(raw_failed.get("estimated_cost_usd") or 0.0),
                        )
                    )
                    raise RuntimeError(response.get("error", "Hermes turn failed"))
                break
            except (
                BrokenPipeError,
                ConnectionError,
                json.JSONDecodeError,
                OSError,
                RuntimeError,
            ) as exc:
                last_error = exc
                if (
                    isinstance(exc, TimeoutError)
                    or self._process is None
                    or self._process.returncode is not None
                ):
                    await self.close()
                if attempt >= self.model.turn_retries or not self._retryable(exc):
                    raise
                delay = min(
                    self.model.retry_initial_s * (2**attempt),
                    self.model.retry_max_s,
                )
                delay += random.uniform(0.0, self.model.retry_jitter_s)
                await asyncio.sleep(delay)
        if response is None:
            raise RuntimeError("Hermes turn failed without a response") from last_error
        raw = response.get("usage") or {}
        usage = Usage(
            input_tokens=int(raw.get("input_tokens") or 0),
            output_tokens=int(raw.get("output_tokens") or 0),
            estimated_cost_usd=float(raw.get("estimated_cost_usd") or 0.0),
        )
        usage.add(retry_usage)
        return HermesTurn(
            text=str(response.get("text") or ""),
            usage=usage,
            completed=bool(response.get("completed", True)),
            exit_reason=str(response.get("exit_reason") or "unknown"),
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
        )
        return not any(marker in message for marker in deterministic)

    async def close(self) -> None:
        """Close the worker gracefully, terminating it if shutdown stalls.

        Calling this method more than once is safe. The process reference is cleared
        before shutdown so the session cannot accidentally reuse a closing worker.

        """
        process = self._process
        self._process = None
        if process is None:
            return
        if process.returncode is None:
            try:
                await self._write_to(process, {"op": "close"})
                await asyncio.wait_for(process.wait(), timeout=5)
            except OSError:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    await process.wait()

    async def _write(self, payload: dict[str, Any]) -> None:
        """Write a protocol message to the active worker.

        Args:
            payload: JSON-serializable worker request.

        Raises:
            RuntimeError: If the session has no active worker process.

        """
        if self._process is None:
            raise RuntimeError("Hermes worker is not running")
        await self._write_to(self._process, payload)

    @staticmethod
    async def _write_to(process: asyncio.subprocess.Process, payload: dict[str, Any]) -> None:
        """Serialize one JSONL request to a specific worker process.

        Args:
            process: Worker process whose standard input receives the request.
            payload: JSON-serializable worker request.

        Raises:
            RuntimeError: If the worker standard-input pipe is unavailable.

        """
        if process.stdin is None:
            raise RuntimeError("Hermes worker stdin is unavailable")
        process.stdin.write((json.dumps(payload) + "\n").encode())
        await process.stdin.drain()

    async def _read(self) -> dict[str, Any]:
        """Read and decode one JSONL response from the active worker.

        Returns:
            Decoded worker response object.

        Raises:
            RuntimeError: If no readable worker exists or the worker exits early.
            json.JSONDecodeError: If the response line is not valid JSON.

        """
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("Hermes worker stdout is unavailable")
        line = await self._process.stdout.readline()
        if not line:
            stderr = ""
            if self._process.stderr is not None:
                stderr = (await self._process.stderr.read()).decode(errors="replace")
            raise RuntimeError(f"Hermes worker exited unexpectedly: {stderr[-4000:]}")
        return cast("dict[str, Any]", json.loads(line))

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
