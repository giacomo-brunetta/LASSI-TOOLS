from pathlib import Path
from types import SimpleNamespace

import graph.container_pool as container_pool
from graph.container_pool import AgentContainer


def _bare_container(tmp_path: Path, *, auto_build: bool) -> AgentContainer:
    container = object.__new__(AgentContainer)
    container.image = "lassi-graph:test"
    container.repo_root = tmp_path
    container.auto_build = auto_build
    return container


def test_auto_build_refreshes_an_existing_image(monkeypatch, tmp_path):
    container = _bare_container(tmp_path, auto_build=True)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(container_pool.subprocess, "run", fake_run)

    container._ensure_image()

    assert calls[0][0] == ["docker", "image", "inspect", "lassi-graph:test"]
    assert calls[1][0][:3] == ["docker", "build", "--quiet"]
    assert calls[1][1]["cwd"] == str(tmp_path)


def test_no_auto_build_uses_an_existing_image(monkeypatch, tmp_path):
    container = _bare_container(tmp_path, auto_build=False)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(container_pool.subprocess, "run", fake_run)

    container._ensure_image()

    assert calls == [
        (["docker", "image", "inspect", "lassi-graph:test"], {"capture_output": True})
    ]
