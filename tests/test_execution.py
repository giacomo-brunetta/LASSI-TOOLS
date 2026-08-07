from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import aiohttp
import pytest
from academy.exchange import LocalExchangeFactory
from academy.manager import Manager
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from multidict import CIMultiDict, CIMultiDictProxy
from yaml import safe_dump, safe_load
from yarl import URL

from lassi_x.cli import _execution_doctor_command
from lassi_x.config import RunConfig
from lassi_x.execution import (
    AcademyExecutionBackend,
    ExecutionBackend,
    ExecutionContext,
    LocalExecutionBackend,
    RemoteCallTimeoutError,
    ResourceUnavailableError,
    _add_academy_send_retry,
    _disable_academy_stream_deadline,
    fetch_bytes,
    put_bytes,
)
from lassi_x.hermes import HermesSession
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


def _http_error(status: int) -> object:
    """Build a realistic aiohttp error; str() on it needs request_info."""
    info = aiohttp.RequestInfo(
        URL("https://exchange.academy-agents.org/message"),
        "PUT",
        CIMultiDictProxy(CIMultiDict()),
    )
    return aiohttp.ClientResponseError(info, (), status=status)


def _retry_transport(errors: list[BaseException]) -> tuple[object, list[object]]:
    """Build a fake transport whose send raises `errors` before succeeding."""
    sent: list[object] = []
    pending = list(errors)

    async def send(message: object) -> None:
        if pending:
            raise pending.pop(0)
        sent.append(message)

    transport = type("Transport", (), {"send": staticmethod(send)})()
    return transport, sent


def test_academy_send_retries_transient_gateway_failure() -> None:
    transport, sent = _retry_transport([_http_error(502), _http_error(503)])
    _add_academy_send_retry(transport, base_delay_s=0)
    asyncio.run(transport.send("response"))
    assert sent == ["response"]


def test_academy_send_retries_dropped_connection() -> None:
    transport, sent = _retry_transport([aiohttp.ClientConnectionError("reset")])
    _add_academy_send_retry(transport, base_delay_s=0)
    asyncio.run(transport.send("response"))
    assert sent == ["response"]


def test_academy_send_does_not_retry_client_error() -> None:
    transport, sent = _retry_transport([_http_error(404), _http_error(404)])
    _add_academy_send_retry(transport, base_delay_s=0)
    with pytest.raises(aiohttp.ClientResponseError):
        asyncio.run(transport.send("response"))
    assert sent == []


def test_academy_send_raises_after_exhausting_attempts() -> None:
    transport, sent = _retry_transport([_http_error(502) for _ in range(3)])
    _add_academy_send_retry(transport, attempts=3, base_delay_s=0)
    with pytest.raises(aiohttp.ClientResponseError):
        asyncio.run(transport.send("response"))
    assert sent == []


def _stalling_backend(release: asyncio.Event) -> AcademyExecutionBackend:
    """Build a backend whose handle answers only once `release` is set."""

    class Handle:
        @staticmethod
        async def execute(request: object) -> str:
            await release.wait()
            return "done"

    return AcademyExecutionBackend(
        Handle(),  # type: ignore[arg-type]
        "wedged-node",
        stall_warn_interval_s=0.01,
    )


def _exec_request(timeout_s: float = 600.0) -> ExecRequest:
    return ExecRequest(workspace="w", argv=["./bench", "--large"], timeout_s=timeout_s)


def test_stalled_remote_call_warns_with_resource_and_command(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def run() -> None:
        release = asyncio.Event()
        backend = _stalling_backend(release)
        call = asyncio.ensure_future(backend.execute(_exec_request()))
        await asyncio.sleep(0.05)
        release.set()
        await call

    with caplog.at_level(logging.WARNING, logger="lassi_x.execution"):
        asyncio.run(run())

    stalls = [record.getMessage() for record in caplog.records if "unanswered" in record.message]
    assert stalls, "a call held open past the interval must warn"
    assert "execute on wedged-node" in stalls[0]
    assert "./bench --large" in stalls[0]


def test_unanswered_remote_call_is_abandoned_not_awaited_forever() -> None:
    async def run() -> None:
        backend = _stalling_backend(asyncio.Event())
        backend.call_timeout_s = 0.05
        with pytest.raises(RemoteCallTimeoutError) as caught:
            await backend.execute(_exec_request(timeout_s=0.01))
        assert caught.value.resource == "wedged-node"
        assert caught.value.op == "execute"

    asyncio.run(run())


def test_resource_is_retired_after_repeated_abandoned_calls() -> None:
    """Two abandoned calls must retire the resource and notify the run."""

    async def run() -> None:
        retired: list[tuple[str, str]] = []
        backend = _stalling_backend(asyncio.Event())
        backend.call_timeout_s = 0.05
        backend.on_dead = lambda resource, detail: retired.append((resource, detail))

        for _ in range(2):
            with pytest.raises(RemoteCallTimeoutError):
                await backend.execute(_exec_request(timeout_s=0.01))
        assert [name for name, _ in retired] == ["wedged-node"]

        # The third call must not wait at all: the point of retirement is that
        # a wedged resource stops costing call_timeout_s per remaining call.
        started = time.monotonic()
        with pytest.raises(ResourceUnavailableError) as caught:
            await backend.execute(_exec_request(timeout_s=600.0))
        assert time.monotonic() - started < 0.05
        assert caught.value.resource == "wedged-node"

    asyncio.run(run())


def test_one_abandoned_call_does_not_retire_a_resource_that_recovers() -> None:
    """A single lost response is survivable, and the streak resets on success."""

    async def run() -> None:
        release = asyncio.Event()
        backend = _stalling_backend(release)
        backend.call_timeout_s = 0.05
        with pytest.raises(RemoteCallTimeoutError):
            await backend.execute(_exec_request(timeout_s=0.01))
        assert backend.dead_detail is None

        release.set()
        await backend.execute(_exec_request())
        release.clear()

        with pytest.raises(RemoteCallTimeoutError):
            await backend.execute(_exec_request(timeout_s=0.01))
        assert backend.dead_detail is None, "success must clear the timeout streak"

    asyncio.run(run())


def test_retirement_can_be_disabled() -> None:
    async def run() -> None:
        backend = _stalling_backend(asyncio.Event())
        backend.call_timeout_s = 0.05
        backend.dead_after_timeouts = 0
        for _ in range(3):
            with pytest.raises(RemoteCallTimeoutError):
                await backend.execute(_exec_request(timeout_s=0.01))
        assert backend.dead_detail is None

    asyncio.run(run())


def test_dead_resource_turn_failure_is_not_retried() -> None:
    """The most expensive thing to retry is a turn that cannot succeed."""
    error = ResourceUnavailableError("a100-node", "2 consecutive calls abandoned")
    assert not HermesSession._retryable(RuntimeError(str(error)))
    assert HermesSession._retryable(RuntimeError("Connection error."))


def test_execute_bound_allows_the_command_its_own_timeout() -> None:
    """A slow-but-answering command must not be cut off by the transport bound."""

    async def run() -> None:
        release = asyncio.Event()
        backend = _stalling_backend(release)
        backend.call_timeout_s = 0.2
        call = asyncio.ensure_future(backend.execute(_exec_request()))
        await asyncio.sleep(0.3)
        assert not call.done(), "bound must include the request's own timeout_s"
        release.set()
        await call

    asyncio.run(run())


def test_completed_remote_call_does_not_warn(caplog: pytest.LogCaptureFixture) -> None:
    async def run() -> None:
        release = asyncio.Event()
        release.set()
        await _stalling_backend(release).execute(_exec_request())
        # Give a leaked watchdog the chance to fire before the loop closes.
        await asyncio.sleep(0.05)

    with caplog.at_level(logging.WARNING, logger="lassi_x.execution"):
        asyncio.run(run())

    assert not [record for record in caplog.records if "unanswered" in record.message]


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


def test_execution_context_activates_and_restores_memory_provider(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["memory"] = {"enabled": True}
    config = RunConfig.model_validate(data)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    home = tmp_path / "hermes"
    home.mkdir()
    (home / "config.yaml").write_text(safe_dump({"memory": {"provider": "honcho"}}))

    async def run() -> None:
        context = await ExecutionContext.start(config, run_dir, hermes_home=home)
        try:
            assert safe_load((home / "config.yaml").read_text())["memory"]["provider"] == "mem0"
        finally:
            await context.close()
        assert safe_load((home / "config.yaml").read_text())["memory"]["provider"] == "honcho"

    asyncio.run(run())
