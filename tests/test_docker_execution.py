from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

import pytest
import yaml

import lassi_x.pipeline as pipeline
from lassi_x.config import DockerExecutionConfig, ExecutionConfig, RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.execution.docker import DockerExecutionBackend
from lassi_x.protocol import ExecRequest, ExecResult
from lassi_x.remote import ops

from .test_config import minimal_config

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> DockerExecutionBackend:
    monkeypatch.setattr(os, "getuid", lambda: 1000)
    monkeypatch.setattr(os, "getgid", lambda: 1000)
    return DockerExecutionBackend(tmp_path, DockerExecutionConfig())


def test_container_policy(backend: DockerExecutionBackend, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_API_KEY", "must-not-be-forwarded")
    command = backend.command(ExecRequest(workspace="c1", argv=["python", "-c", "pass"]), "test")
    for flag in [
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--pull=never",
        "--security-opt=no-new-privileges",
    ]:
        assert flag in command
    assert command[command.index("--user") + 1] == "1000:1000"
    assert "SECRET_API_KEY" not in " ".join(command)
    assert "docker.sock" not in " ".join(command)
    assert command[-4:] == ["lassi-x-cpu:0.1", "python", "-c", "pass"]
    with pytest.raises(ValueError, match="environment variables"):
        backend.command(ExecRequest(workspace="c1", argv=["python"], env={"PATH": "/tmp"}), "test")


def test_validation_mounts_readonly(backend: DockerExecutionBackend) -> None:
    (backend.workspace_root / "c1/reference").mkdir(parents=True)
    command = backend.command(
        ExecRequest(
            workspace="c1",
            argv=["/usr/local/bin/python", "-m", "lassi_x.runner", "--module", "candidate.py"],
        ),
        "test",
    )
    mounts = [command[i + 1] for i, item in enumerate(command) if item == "--mount"]
    assert any(mount.endswith("dst=/workspace,readonly") for mount in mounts)
    assert any(mount.endswith("dst=/workspace/.lassi") for mount in mounts)
    command = backend.command(ExecRequest(workspace="c1", argv=["sh", "-c", "true"]), "test")
    assert any(item.endswith("dst=/workspace/reference,readonly") for item in command)


@pytest.mark.parametrize("failure", ["normal", "timeout", "cancelled"])
def test_cleanup_always_runs(
    backend: DockerExecutionBackend, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    removed = []

    async def fake_exec(root: Path, request: ExecRequest) -> ExecResult:
        assert request.argv[:2] == ["docker", "run"]
        assert request.env == {}
        if failure == "cancelled":
            raise asyncio.CancelledError
        return ExecResult(
            workspace=request.workspace, exit_code=0, timed_out=failure == "timeout", duration_s=0
        )

    async def fake_remove(name: str) -> None:
        removed.append(name)

    monkeypatch.setattr(ops, "run_exec", fake_exec)
    monkeypatch.setattr(backend, "_remove", fake_remove)

    def task() -> ExecResult:
        return asyncio.run(
            backend.execute(ExecRequest(workspace="c1", argv=["python", "-c", "pass"]))
        )

    if failure == "cancelled":
        with pytest.raises(asyncio.CancelledError):
            task()
    else:
        task()
    assert len(removed) == 1
    assert removed[0].startswith("lassi-cpu-")


def test_docker_rejects_remote_resources() -> None:
    assert ExecutionConfig(mode="docker").docker.memory_mb == 4096
    with pytest.raises(ValueError, match="omit execution.resources"):
        ExecutionConfig.model_validate({"mode": "docker", "resources": {"cpu": {}}})


def test_cpu_stop_preserves_docker_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = minimal_config(tmp_path)
    data["execution"] = {"mode": "docker", "docker": {"cpus": 1.0}}
    config_path = tmp_path / "run.yaml"
    config_path.write_text(yaml.safe_dump(data))
    observed = []

    async def fake_start(config: RunConfig, run_dir: Path) -> ExecutionContext:
        observed.append(config.execution)
        raise RuntimeError("stop after inspecting selected backend")

    monkeypatch.setattr(pipeline, "require_automation_skills", lambda: None)
    monkeypatch.setattr(ExecutionContext, "start", fake_start)
    assert asyncio.run(pipeline.run_pipeline(config_path, until="cpu-verified"))[0] == 1
    assert observed[0].mode == "docker"
    assert observed[0].docker.cpus == 1.0
