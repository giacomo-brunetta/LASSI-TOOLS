"""GPU restart must not repeat paid CPU generation or silently replay GPU work."""

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml


def test_gpu_restart_checkpoint_guards(tmp_path: Path) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "experiments/repair-campaigns/rerun_precision_models.py"
    )
    resume = runpy.run_path(str(script))["gpu_resume_state"]
    resume.__globals__["OUTPUT"] = tmp_path
    resume.__globals__["_baseline_contract"] = lambda config: {"task": "original"}
    resume.__globals__["RunConfig"] = type("Config", (), {"load": staticmethod(lambda p: None)})
    resume.__globals__["large_config"] = lambda entry: None
    cpu = tmp_path / "cpu/run.json"
    cpu.parent.mkdir()
    (cpu.parent / "cpu-baseline").mkdir()
    manifest = cpu.parent / "cpu-baseline/manifest.json"
    manifest.write_text(json.dumps({"contract": {"task": "original"}, "files": {}}))
    cpu.write_text(json.dumps({"status": "cpu_verified"}))
    state = {
        "status": "gpu_blocked",
        "cpu_runs": {"terra/test": str(cpu)},
        "gpu_runs": {},
    }
    (tmp_path / "status.json").write_text(json.dumps(state))
    plan = {
        "entries": [
            {
                "model": "terra",
                "kernel": "test",
                "root": str(tmp_path),
                "configs": {"gpu": "unused.yaml"},
            }
        ]
    }
    assert resume(plan) == state
    state.update(
        status="interrupted",
        phase="mini_gpu_compatibility",
        error="RuntimeError: GPU invocation produced no terminal record: terra/test",
    )
    (tmp_path / "status.json").write_text(json.dumps(state))
    attempt = tmp_path / "gpu/runs/test/attempt"
    attempt.mkdir(parents=True)
    (attempt / "resolved-config.yaml").write_text("{}")
    assert resume(plan) == state
    manifest.write_text(json.dumps({"contract": {"task": "different"}, "files": {}}))
    with pytest.raises(RuntimeError, match="contract mismatch"):
        resume(plan)
    manifest.write_text(json.dumps({"contract": {"task": "original"}, "files": {}}))
    cpu.write_text(json.dumps({"status": "failed", "notes": "quota exceeded"}))
    with pytest.raises(RuntimeError, match="service interruption"):
        resume(plan)
    cpu.write_text(json.dumps({"status": "cpu_verified"}))
    gpu = tmp_path / "gpu/runs/test/attempt/run.json"
    gpu.parent.mkdir(parents=True, exist_ok=True)
    gpu.write_text("{}")
    with pytest.raises(RuntimeError, match="stage-specific recovery"):
        resume(plan)
    state.update(
        status="interrupted",
        phase="large_evaluation_only",
        gpu_runs={"terra/test": str(gpu)},
    )
    (tmp_path / "status.json").write_text(json.dumps(state))
    gpu.write_text(json.dumps({"checkpoint": {"completed_stages": ["finalize"]}}))
    (attempt / "cpu-baseline-provenance.json").write_text(
        json.dumps(
            {
                "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            }
        )
    )
    assert resume(plan) == state
    gpu.write_text(json.dumps({"checkpoint": {"completed_stages": []}}))
    with pytest.raises(RuntimeError, match="stage-specific recovery"):
        resume(plan)
    state["status"] = "running"
    (tmp_path / "status.json").write_text(json.dumps(state))
    with pytest.raises(RuntimeError, match="untouched GPU preflight"):
        resume(plan)


def test_large_config_uses_current_model_count(tmp_path: Path) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "experiments/repair-campaigns/rerun_precision_models.py"
    )
    make_config = runpy.run_path(str(script))["large_config"]
    make_config.__globals__["FROZEN"] = tmp_path
    template = {
        "models": {"candidates": ["old", "old"]},
        "arena": {"candidates": 2},
        "execution": {"resources": {"a100": {}}},
        "measure": {"backends": [{}]},
    }
    template_path = tmp_path / "template.yaml"
    template_path.write_text(yaml.safe_dump(template))
    (tmp_path / "campaign.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "name": "test",
                        "config": str(template_path),
                        "references": {},
                    }
                ]
            }
        )
    )
    mini_path = tmp_path / "mini.yaml"
    mini_path.write_text(yaml.safe_dump({"models": {"candidates": ["new"] * 3}}))

    def validate(config: dict[str, Any]) -> None:
        assert config["arena"]["candidates"] == len(config["models"]["candidates"])

    make_config.__globals__["RunConfig"] = SimpleNamespace(model_validate=validate)
    config, _ = make_config(
        {
            "model": "terra",
            "kernel": "test",
            "root": str(tmp_path),
            "configs": {"gpu": str(mini_path)},
        }
    )
    assert config["arena"]["candidates"] == 3
    assert config["compensation"]["enabled"] is False
    assert config["measure"]["backends"][0]["precision_audit"] == "enforce"
    assert not (tmp_path / "large").exists()


def test_resume_large_does_not_rerun_cpu_or_mini(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "experiments/repair-campaigns/rerun_precision_models.py"
    )
    run = runpy.run_path(str(script))["run"]
    namespace = run.__globals__
    namespace["OUTPUT"] = tmp_path
    cpu = tmp_path / "cpu.json"
    cpu.write_text(json.dumps({"status": "cpu_verified"}))
    gpu = tmp_path / "gpu.json"
    gpu.write_text(json.dumps({"status": "partial"}))
    (tmp_path / "campaign.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "model": "terra",
                        "kernel": "test",
                        "root": str(tmp_path),
                        "configs": {"gpu": "gpu.yaml"},
                    }
                ]
            }
        )
    )
    state = {
        "status": "interrupted",
        "phase": "large_evaluation_only",
        "cpu_runs": {"terra/test": str(cpu)},
        "gpu_runs": {"terra/test": str(gpu)},
        "completed": [{"case": "terra/test", "stage": "mini_gpu", "status": "partial"}],
    }
    namespace["gpu_resume_state"] = lambda plan: deepcopy(state)
    namespace["large_plan"] = lambda entry, path: tmp_path / "large/campaign.json"
    commands = []

    def command(argv: list[str], **kwargs: Any) -> SimpleNamespace:
        commands.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(namespace["subprocess"], "run", command)
    assert run(resume_gpu=True) == 0
    assert len(commands) == 2  # Endpoint doctor, then deterministic LARGE evaluator.
    assert "doctor" in commands[0]
    assert "--baseline-only" in commands[1]
    assert not any("--from-cpu-baseline" in argv for argv in commands)
    saved = json.loads((tmp_path / "status.json").read_text())
    assert saved["status"] == "completed"
    assert sum(c["stage"] == "mini_gpu" for c in saved["completed"]) == 1
