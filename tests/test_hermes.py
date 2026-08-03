from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

from lassi_x.config import ModelConfig
from lassi_x.hermes import HermesSession
from lassi_x.hermes_worker import create_agent, scrub_sensitive
from lassi_x.protocol import (
    TurnUsage,
    WireModel,
    WorkerFailure,
    WorkerInit,
    WorkerResponse,
    WorkerTurn,
)

if TYPE_CHECKING:
    from pathlib import Path


class RetrySession(HermesSession):
    def __init__(self, tmp_path: Path) -> None:
        super().__init__(
            ModelConfig(
                model="test",
                turn_retries=1,
                retry_initial_s=0,
                retry_jitter_s=0,
            ),
            cwd=tmp_path,
            system_prompt="role",
            toolsets=[],
            role="test",
        )
        self.reads = 0
        self.writes: list[WireModel] = []

    async def start(self) -> None:
        return None

    async def _write(self, message: WireModel) -> None:
        self.writes.append(message)

    async def _read(self) -> WorkerResponse:
        self.reads += 1
        if self.reads == 1:
            return WorkerFailure(error="HTTP 503 service unavailable")
        return WorkerTurn(
            text="finished",
            completed=False,
            exit_reason="max_iterations_reached(2/2)",
            usage=TurnUsage(input_tokens=3, output_tokens=4),
        )


def test_agent_turn_retries_and_preserves_exit_reason(tmp_path: Path) -> None:
    session = RetrySession(tmp_path)
    turn = asyncio.run(session.send("implement"))
    assert len(session.writes) == 2
    assert turn.text == "finished"
    assert not turn.completed
    assert turn.exit_reason == "max_iterations_reached(2/2)"
    assert turn.attempts == 2


def test_worker_diagnostics_scrub_resolved_credentials() -> None:
    secret = "secret-token-value"
    scrubbed = scrub_sensitive(
        f"provider rejected api_key={secret}\ntrace includes {secret}", [secret]
    )
    assert secret not in scrubbed
    assert scrubbed.count("[REDACTED]") == 2


def test_worker_discovers_mcp_tools_before_constructing_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    fake_run_agent = ModuleType("run_agent")
    fake_mcp_tool = ModuleType("tools.mcp_tool")

    def discover() -> list[str]:
        events.append("discover")
        return ["mcp__lassi_x_c1__write_file"]

    def prefixed(server: str, tool: str) -> str:
        return f"mcp__{server.replace('-', '_')}__{tool}"

    class FakeAgent:
        def __init__(self, **_: object) -> None:
            events.append("construct")

    fake_run_agent.AIAgent = FakeAgent  # type: ignore[attr-defined]
    fake_mcp_tool.discover_mcp_tools = discover  # type: ignore[attr-defined]
    fake_mcp_tool.mcp_prefixed_tool_name = prefixed  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)
    monkeypatch.setitem(sys.modules, "tools.mcp_tool", fake_mcp_tool)

    request = WorkerInit(model="test", role="candidate", toolsets=["lassi-x-c1"])
    assert isinstance(create_agent(request, None), FakeAgent)
    assert events == ["discover", "construct"]


def test_worker_rejects_missing_workspace_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_run_agent = ModuleType("run_agent")
    fake_mcp_tool = ModuleType("tools.mcp_tool")
    fake_run_agent.AIAgent = object  # type: ignore[attr-defined]
    fake_mcp_tool.discover_mcp_tools = lambda: []  # type: ignore[attr-defined]
    fake_mcp_tool.mcp_prefixed_tool_name = (  # type: ignore[attr-defined]
        lambda server, tool: f"mcp__{server.replace('-', '_')}__{tool}"
    )
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)
    monkeypatch.setitem(sys.modules, "tools.mcp_tool", fake_mcp_tool)

    request = WorkerInit(model="test", role="candidate", toolsets=["lassi-x-c1"])
    with pytest.raises(RuntimeError, match="did not discover"):
        create_agent(request, None)


def test_worker_does_not_accept_foreign_mcp_tools_for_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_run_agent = ModuleType("run_agent")
    fake_mcp_tool = ModuleType("tools.mcp_tool")
    fake_run_agent.AIAgent = object  # type: ignore[attr-defined]
    fake_mcp_tool.discover_mcp_tools = (  # type: ignore[attr-defined]
        lambda: ["mcp__unrelated__write_file"]
    )
    fake_mcp_tool.mcp_prefixed_tool_name = (  # type: ignore[attr-defined]
        lambda server, tool: f"mcp__{server.replace('-', '_')}__{tool}"
    )
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)
    monkeypatch.setitem(sys.modules, "tools.mcp_tool", fake_mcp_tool)

    request = WorkerInit(model="test", role="candidate", toolsets=["lassi-x-c1"])
    with pytest.raises(RuntimeError, match="lassi-x-c1"):
        create_agent(request, None)


class TimeoutSession(RetrySession):
    def __init__(self, tmp_path: Path) -> None:
        super().__init__(tmp_path)
        self.model.turn_retries = 0
        self.model.turn_timeout_s = 0.01
        self.closed = False

    async def _read(self) -> WorkerResponse:
        await asyncio.sleep(1)
        return WorkerTurn(text="late", usage=TurnUsage())

    async def close(self) -> None:
        self.closed = True


def test_agent_turn_timeout_closes_worker(tmp_path: Path) -> None:
    session = TimeoutSession(tmp_path)
    with pytest.raises(TimeoutError):
        asyncio.run(session.send("never finishes"))
    assert session.closed
