from __future__ import annotations

import asyncio
import json
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import yaml
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from lassi_x.execution import LocalExecutionBackend
from lassi_x.hermes_config import (
    enable_memory_provider,
    register_workspace_servers,
    registered_lassi_servers,
    restore_memory_provider,
    server_name,
    unregister_workspace_servers,
)
from lassi_x.mcp_server import WORKSPACE_HEADER, LassiMCPServer, MCPServerRunner

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


@asynccontextmanager
async def _client(url: str, workspace: str | None) -> AsyncIterator[ClientSession]:
    headers = {WORKSPACE_HEADER: workspace} if workspace else {}
    async with (
        create_mcp_http_client(headers=headers) as http,
        streamable_http_client(url, http_client=http) as streams,
        ClientSession(streams[0], streams[1]) as client,
    ):
        await client.initialize()
        yield client


def _text(result: Any) -> str:
    return str(result.content[0].text)


def test_mcp_tools_are_workspace_pinned_and_resource_selectable(tmp_path: Path) -> None:
    default_root = tmp_path / "default"
    gpu_root = tmp_path / "gpu"
    server = LassiMCPServer(
        {
            "default": LocalExecutionBackend(default_root, "default"),
            "gpu": LocalExecutionBackend(gpu_root, "gpu"),
        },
        default_resource="default",
    )

    async def run() -> None:
        async with MCPServerRunner(server) as runner:
            async with _client(runner.url, "c1") as client:
                tools = {tool.name for tool in (await client.list_tools()).tools}
                assert tools == {
                    "list_resources",
                    "run_command",
                    "write_file",
                    "read_file",
                    "list_files",
                }
                await client.call_tool("write_file", {"path": "main.py", "content": "print('hi')"})
                run = await client.call_tool(
                    "run_command", {"command": [sys.executable, "main.py"]}
                )
                assert "exit_code: 0" in _text(run)
                assert "hi" in _text(run)
                read = await client.call_tool("read_file", {"path": "main.py"})
                assert "print('hi')" in _text(read)
                listing = await client.call_tool("list_files", {})
                assert "main.py" in _text(listing)
                # The same call with resource targeting lands on the other root.
                await client.call_tool(
                    "write_file",
                    {"path": "gpu.txt", "content": "gpu-data", "resource": "gpu"},
                )
                resources = json.loads(_text(await client.call_tool("list_resources", {})))
                assert set(resources["resources"]) == {"default", "gpu"}
                assert resources["default_resource"] == "default"
            assert (default_root / "c1" / "main.py").is_file()
            assert (gpu_root / "c1" / "gpu.txt").read_text() == "gpu-data"
            assert not (default_root / "c1" / "gpu.txt").exists()

    asyncio.run(run())


def test_mcp_tools_reject_unpinned_connections_and_unknown_resources(tmp_path: Path) -> None:
    server = LassiMCPServer(
        {"default": LocalExecutionBackend(tmp_path, "default")},
        default_resource="default",
    )

    async def run() -> None:
        async with MCPServerRunner(server) as runner:
            async with _client(runner.url, None) as client:
                result = await client.call_tool("write_file", {"path": "x.txt", "content": "x"})
                assert result.isError
                assert WORKSPACE_HEADER in _text(result)
            async with _client(runner.url, "c1") as client:
                result = await client.call_tool(
                    "run_command", {"command": ["ls"], "resource": "nope"}
                )
                assert result.isError
                assert "unknown resource" in _text(result)
                escape = await client.call_tool("read_file", {"path": "../outside.txt"})
                assert escape.isError

    asyncio.run(run())


def test_hermes_registration_round_trip_preserves_foreign_entries(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    home.mkdir()
    (home / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "default_model": "gpt-x",
                "mcp_servers": {"github": {"command": "npx", "args": ["server-github"]}},
            }
        )
    )
    names = register_workspace_servers(
        "http://127.0.0.1:9999/mcp", ["c1", "c2"], home=home, timeout_s=450
    )
    assert names == [server_name("c1"), server_name("c2")]
    data = yaml.safe_load((home / "config.yaml").read_text())
    assert data["default_model"] == "gpt-x"
    assert set(data["mcp_servers"]) == {"github", "lassi-x-c1", "lassi-x-c2"}
    entry = data["mcp_servers"]["lassi-x-c1"]
    assert entry["url"] == "http://127.0.0.1:9999/mcp"
    assert entry["headers"] == {WORKSPACE_HEADER: "c1"}
    assert entry["timeout"] == 450
    assert entry["tools"] == {"resources": False, "prompts": False}
    assert set(registered_lassi_servers(home)) == {"lassi-x-c1", "lassi-x-c2"}

    removed = unregister_workspace_servers([*names, "github"], home=home)
    assert removed == names
    data = yaml.safe_load((home / "config.yaml").read_text())
    assert set(data["mcp_servers"]) == {"github"}
    assert registered_lassi_servers(home) == {}


def test_memory_provider_enable_and_restore_preserve_other_settings(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    home.mkdir()
    (home / "config.yaml").write_text(
        yaml.safe_dump({"default_model": "gpt-x", "memory": {"memory_enabled": True}})
    )
    previous = enable_memory_provider(home=home)
    assert previous is None
    data = yaml.safe_load((home / "config.yaml").read_text())
    assert data["memory"]["provider"] == "mem0"
    assert data["memory"]["memory_enabled"] is True
    assert data["default_model"] == "gpt-x"

    restore_memory_provider(previous, home=home)
    data = yaml.safe_load((home / "config.yaml").read_text())
    assert "provider" not in data["memory"]
    assert data["memory"]["memory_enabled"] is True


def test_memory_provider_restore_returns_prior_provider(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    home.mkdir()
    (home / "config.yaml").write_text(yaml.safe_dump({"memory": {"provider": "honcho"}}))
    previous = enable_memory_provider(home=home)
    assert previous == "honcho"
    assert yaml.safe_load((home / "config.yaml").read_text())["memory"]["provider"] == "mem0"

    restore_memory_provider(previous, home=home)
    assert yaml.safe_load((home / "config.yaml").read_text())["memory"]["provider"] == "honcho"


def test_memory_provider_restore_removes_empty_section_in_fresh_home(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    previous = enable_memory_provider(home=home)
    assert previous is None
    assert yaml.safe_load((home / "config.yaml").read_text()) == {"memory": {"provider": "mem0"}}

    restore_memory_provider(previous, home=home)
    assert yaml.safe_load((home / "config.yaml").read_text()) == {}
