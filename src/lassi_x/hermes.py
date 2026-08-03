from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from .types import Usage

if TYPE_CHECKING:
    from .config import ModelConfig


@dataclass(slots=True)
class HermesTurn:
    text: str
    usage: Usage


class HermesSession:
    """One persistent Hermes worker process and conversation."""

    def __init__(
        self,
        model: ModelConfig,
        *,
        cwd: Path,
        system_prompt: str,
        toolsets: list[str],
        role: str,
    ) -> None:
        self.model = model
        self.cwd = cwd
        self.system_prompt = system_prompt
        self.toolsets = toolsets
        self.role = role
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> None:
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
        await self.start()
        await self._write({"op": "send", "prompt": prompt})
        response = await self._read()
        if not response.get("ok"):
            raise RuntimeError(response.get("error", "Hermes turn failed"))
        raw = response.get("usage") or {}
        return HermesTurn(
            text=str(response.get("text") or ""),
            usage=Usage(
                input_tokens=int(raw.get("input_tokens") or 0),
                output_tokens=int(raw.get("output_tokens") or 0),
                estimated_cost_usd=float(raw.get("estimated_cost_usd") or 0.0),
            ),
        )

    async def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.returncode is None:
            try:
                await self._write_to(process, {"op": "close"})
                await asyncio.wait_for(process.wait(), timeout=5)
            except (TimeoutError, BrokenPipeError):
                process.terminate()
                await process.wait()

    async def _write(self, payload: dict[str, Any]) -> None:
        if self._process is None:
            raise RuntimeError("Hermes worker is not running")
        await self._write_to(self._process, payload)

    @staticmethod
    async def _write_to(process: asyncio.subprocess.Process, payload: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("Hermes worker stdin is unavailable")
        process.stdin.write((json.dumps(payload) + "\n").encode())
        await process.stdin.drain()

    async def _read(self) -> dict[str, Any]:
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
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
