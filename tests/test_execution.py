from __future__ import annotations

import asyncio
import base64
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from academy.exchange import LocalExchangeFactory
from academy.manager import Manager

from lassi_x.execution import (
    AcademyExecutionBackend,
    ExecutionBackend,
    LocalExecutionBackend,
)
from lassi_x.protocol import ExecRequest, FileGet, FilePut, ListDir
from lassi_x.remote import ExecutionAgent
from lassi_x.remote.ops import resolve_member

if TYPE_CHECKING:
    from pathlib import Path


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


def test_resolve_member_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "c1"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "link").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes the workspace"):
        resolve_member(workspace, "link/file.txt")
