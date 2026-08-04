from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import pytest
from academy.exchange import LocalExchangeFactory
from academy.manager import Manager
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from yaml import safe_dump, safe_load

from lassi_x.cli import _execution_doctor_command
from lassi_x.config import RunConfig
from lassi_x.execution import (
    AcademyExecutionBackend,
    ExecutionBackend,
    ExecutionContext,
    LocalExecutionBackend,
    _disable_academy_stream_deadline,
    fetch_bytes,
    put_bytes,
)
from lassi_x.mcp_server import WORKSPACE_HEADER
from lassi_x.protocol import ExecRequest, FileGet, FilePut, ListDir
from lassi_x.remote import ExecutionAgent
from lassi_x.remote.ops import resolve_member

from .test_config import minimal_config

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


@asynccontextmanager
async def _mcp_client(url: str, workspace: str) -> AsyncIterator[ClientSession]:
    http = create_mcp_http_client(headers={WORKSPACE_HEADER: workspace})
    async with (
        http,
        streamable_http_client(url, http_client=http) as streams,
        ClientSession(streams[0], streams[1]) as client,
    ):
        await client.initialize()
        yield client


async def _exercise_backend(backend: ExecutionBackend) -> None:
    """Run one write-execute-read cycle through any execution backend."""
    put = await backend.put_file(FilePut(workspace="c1", path="job/main.py", text="print(6 * 7)"))
    assert put.size_bytes == len(b"print(6 * 7)")
    result = await backend.execute(
        ExecRequest(workspace="c1", argv=[sys.executable, "job/main.py"])
    )
    assert result.ok
    assert result.stdout.strip() == "42"
    listing = await backend.list_dir(ListDir(workspace="c1", path="job"))
    assert [entry.name for entry in listing.entries] == ["main.py"]
    content = await backend.get_file(FileGet(workspace="c1", path="job/main.py"))
    assert content.encoding == "utf-8"
    assert content.content == "print(6 * 7)"
    assert content.sha256 == put.sha256


def test_local_backend_write_execute_read_cycle(tmp_path: Path) -> None:
    asyncio.run(_exercise_backend(LocalExecutionBackend(tmp_path)))


def test_academy_stream_has_no_total_or_read_deadline() -> None:
    session = type("Session", (), {"_timeout": object()})()
    transport = type("Transport", (), {"_session": session})()
    _disable_academy_stream_deadline(transport)
    timeout = vars(session)["_timeout"]
    assert timeout.total is None
    assert timeout.sock_connect == 60
    assert timeout.sock_read is None


def test_academy_backend_write_execute_read_cycle(tmp_path: Path) -> None:
    async def run() -> None:
        async with await Manager.from_exchange_factory(
            factory=LocalExchangeFactory(),
            executors=ThreadPoolExecutor(max_workers=2),
        ) as manager:
            handle = await manager.launch(ExecutionAgent, args=(str(tmp_path), "test-resource"))
            backend = AcademyExecutionBackend(handle)
            await _exercise_backend(backend)
            report = await backend.handshake()
            assert report.resource == "test-resource"
            assert report.workspace_root == str(tmp_path.resolve())
            assert report.lassi_x_version
            await manager.shutdown(handle, blocking=True)

    asyncio.run(run())


def test_execute_reports_timeout_without_raising(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    request = ExecRequest(
        workspace="c1",
        argv=[sys.executable, "-c", "import time; time.sleep(60)"],
        timeout_s=0.2,
    )
    result = asyncio.run(backend.execute(request))
    assert result.timed_out
    assert result.exit_code is None
    assert not result.ok
    assert result.duration_s < 30


def test_execute_reports_missing_binary_as_result(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    result = asyncio.run(
        backend.execute(ExecRequest(workspace="c1", argv=["lassi-x-no-such-binary"]))
    )
    assert result.exit_code is None
    assert "failed to launch" in result.stderr


def test_execute_truncates_oversized_output(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    request = ExecRequest(
        workspace="c1",
        argv=[sys.executable, "-c", "print('x' * 400_000)"],
    )
    result = asyncio.run(backend.execute(request))
    assert result.ok
    assert result.stdout_truncated
    assert len(result.stdout) <= 256 * 1024


def test_execute_honors_cwd_env_and_stdin(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    request = ExecRequest(
        workspace="c1",
        argv=[
            sys.executable,
            "-c",
            "import os, sys, pathlib; "
            "print(pathlib.Path.cwd().name, os.environ['LASSI_TEST'], sys.stdin.read())",
        ],
        cwd="sub",
        env={"LASSI_TEST": "on"},
        stdin_text="fed",
    )
    result = asyncio.run(backend.execute(request))
    assert result.ok
    assert result.stdout.split() == ["sub", "on", "fed"]


def test_binary_files_round_trip_as_base64(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    payload = bytes(range(256))
    put = FilePut(
        workspace="c1",
        path="blob.bin",
        content_b64=base64.b64encode(payload).decode(),
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    stat = asyncio.run(backend.put_file(put))
    assert stat.size_bytes == 256
    content = asyncio.run(backend.get_file(FileGet(workspace="c1", path="blob.bin")))
    assert content.encoding == "base64"
    assert base64.b64decode(content.content) == payload


def test_put_file_rejects_digest_mismatch(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    put = FilePut(workspace="c1", path="a.txt", text="hello", sha256="0" * 64)
    with pytest.raises(ValueError, match="digest mismatch"):
        asyncio.run(backend.put_file(put))


def test_get_file_reports_truncation(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    asyncio.run(backend.put_file(FilePut(workspace="c1", path="big.txt", text="abcdef")))
    content = asyncio.run(backend.get_file(FileGet(workspace="c1", path="big.txt", max_bytes=4)))
    assert content.truncated
    assert content.content == "abcd"
    assert content.size_bytes == 4


def test_ops_confine_paths_even_when_schema_validation_is_bypassed(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    hostile = FileGet.model_construct(
        schema_version=1, workspace="c1", path="../secret", max_bytes=100
    )
    with pytest.raises(ValueError, match="escapes the workspace"):
        asyncio.run(backend.get_file(hostile))


def test_execution_context_serves_and_cleans_up_registered_workspaces(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["execution"] = {"mode": "academy"}
    config = RunConfig.model_validate(data)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    home = tmp_path / "hermes"

    async def run() -> None:
        context = await ExecutionContext.start(config, run_dir, hermes_home=home)
        try:
            toolset = context.register_workspace("c9")
            assert toolset == "lassi-x-c9"
            registered = safe_load((home / "config.yaml").read_text())["mcp_servers"]
            assert registered[toolset]["url"] == context.runner.url
            assert registered[toolset]["headers"] == {WORKSPACE_HEADER: "c9"}
            async with _mcp_client(context.runner.url, "c9") as client:
                result = await client.call_tool(
                    "write_file", {"path": "hello.txt", "content": "via academy"}
                )
                assert not result.isError
            assert context.workspace_dir("c9").joinpath("hello.txt").read_text() == "via academy"
            handshakes = await context.handshakes()
            assert set(handshakes) == {"local"}
        finally:
            await context.close()
        assert safe_load((home / "config.yaml").read_text()).get("mcp_servers") is None

    asyncio.run(run())


def test_fetch_bytes_reassembles_chunked_reads(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    payload = bytes(range(256)) * 40 + b"tail"
    asyncio.run(
        backend.put_file(
            FilePut(
                workspace="c1",
                path="big.bin",
                content_b64=base64.b64encode(payload).decode(),
            )
        )
    )
    fetched = asyncio.run(fetch_bytes(backend, "c1", "big.bin", chunk_size=1000))
    assert fetched == payload


def test_put_bytes_chunks_and_atomically_reassembles_large_upload(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path)
    payload = bytes(range(256)) * 40 + b"tail"
    asyncio.run(put_bytes(backend, "c1", "nested/big.bin", payload, chunk_size=1000))
    assert (tmp_path / "c1" / "nested" / "big.bin").read_bytes() == payload
    assert not list((tmp_path / "c1").glob(".lassi-transfer-*"))


def test_handshake_reports_python_executable(tmp_path: Path) -> None:
    backend = LocalExecutionBackend(tmp_path, "here")
    report = asyncio.run(backend.cached_handshake())
    assert report.python_executable == sys.executable
    assert asyncio.run(backend.cached_handshake()) is report


def test_execution_doctor_reports_resources(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(safe_dump(minimal_config(tmp_path)))
    args = argparse.Namespace(config=config_path, json=True)
    code = asyncio.run(_execution_doctor_command(args))
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"]
    assert payload["mode"] == "local"
    assert payload["resources"]["local"]["python_executable"]


def test_resolve_member_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "c1"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "link").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes the workspace"):
        resolve_member(workspace, "link/file.txt")
