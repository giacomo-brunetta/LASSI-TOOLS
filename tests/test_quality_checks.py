"""Keep local quality coverage aligned with a clean CI checkout."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/check_quality.py"
spec = importlib.util.spec_from_file_location("check_quality", SCRIPT)
assert spec and spec.loader
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


def test_quality_includes_new_sources_and_versioned_archive_scripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    files = [
        "lassi_x/existing.py",
        "lassi_x/new.py",
        "docs/experiments/frozen/report.py",
        "docs/experiments/local/report.py",
        "tests/new test.py",
        "removed.py",
    ]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pass\n")
    subprocess.run(
        ["git", "add", "lassi_x/existing.py", "docs/experiments/frozen/report.py", "removed.py"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "removed.py").unlink()
    monkeypatch.setattr(quality, "ROOT", tmp_path)
    assert quality.python_files() == [
        "docs/experiments/frozen/report.py",
        "lassi_x/existing.py",
        "lassi_x/new.py",
        "tests/new test.py",
    ]


def test_quality_failure_cannot_be_hidden_by_later_passing_checks(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if len(calls) == 1 else 0)

    monkeypatch.setattr(quality, "python_files", lambda: ["candidate.py"])
    monkeypatch.setattr(quality.subprocess, "run", run)
    monkeypatch.setattr(quality.sys, "argv", ["check_quality.py"])
    assert quality.main() == 1
    assert [command[2:] for command in calls] == [
        ["ruff", "check", "candidate.py"],
        ["ruff", "format", "--check", "candidate.py"],
        ["mypy"],
        ["pytest"],
    ]
    output = capsys.readouterr().out
    assert "lint: FAIL" in output
    assert "tests: PASS" in output
