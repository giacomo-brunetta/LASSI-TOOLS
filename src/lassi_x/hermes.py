from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .protocol import (
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
    from .config import ModelConfig


@dataclass(slots=True)
class HermesTurn:
    """Normalized result from one Hermes conversation turn.

    Attributes:
        text: Final textual response produced by the agent.
        usage: Token and estimated-cost delta attributed to this turn.

    """

    text: str
    usage: Usage


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
        :class:`~lassi_x.protocol.WorkerInit` message containing model, credential-source,
        prompt, and toolset configuration.

        Raises:
            OSError: If the Python worker process cannot be created.
            RuntimeError: If the worker rejects initialization or exits unexpectedly.
            pydantic.ValidationError: If the worker returns malformed protocol data.

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
        )
        await self._write(
            WorkerInit(
                model=self.model.model,
                provider=self.model.provider,
                base_url=self.model.base_url,
                api_mode=self.model.api_mode,
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
            )
        )
        response = await self._read()
        if isinstance(response, WorkerFailure):
            await self.close()
            raise RuntimeError(response.error)
        if not isinstance(response, WorkerReady):
            await self.close()
            raise RuntimeError(f"unexpected worker initialization response: {response.kind}")

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
        await self.start()
        await self._write(WorkerSend(prompt=prompt))
        response = await self._read()
        if isinstance(response, WorkerFailure):
            raise RuntimeError(response.error)
        if not isinstance(response, WorkerTurn):
            raise RuntimeError(f"unexpected worker turn response: {response.kind}")
        return HermesTurn(
            text=response.text,
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                estimated_cost_usd=response.usage.estimated_cost_usd,
            ),
        )

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
                await self._write_to(process, WorkerClose())
                await asyncio.wait_for(process.wait(), timeout=5)
            except (TimeoutError, BrokenPipeError):
                process.terminate()
                await process.wait()

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
        line = await self._process.stdout.readline()
        if not line:
            stderr = ""
            if self._process.stderr is not None:
                stderr = (await self._process.stderr.read()).decode(errors="replace")
            raise RuntimeError(f"Hermes worker exited unexpectedly: {stderr[-4000:]}")
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
