"""Fresh Terra Deriche only: CPU translation, MINI GPU ports, frozen LARGE evaluation.

No numerical-repair campaign or other kernel is launched. Quota errors stop the queue.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lassi_x.artifacts import write_json
from lassi_x.config import RunConfig
from lassi_x.dataset_specialization import read_profile, specialize_source
from lassi_x.interruptions import model_service_interrupted

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "runs/terra-deriche-strict-rerun-20261016"
OLD = REPO / "runs/a100-terra-medium-20261010"
FROZEN = REPO / "runs/a100-clean-gpu-repairs-20261016"


def prepare() -> None:
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    original = yaml.safe_load((OLD / "configs/polybench-deriche.yaml").read_text())
    models = yaml.safe_load((REPO / "experiments/cpu-generation/models/terra.yaml").read_text())[
        "models"
    ]
    original["models"] = {**models, "compatibility": models["planner"]}
    original["arena"]["candidates"] = 3
    original["scheduler"] = {"max_candidate_flows": 1, "max_model_sessions": 1}
    original["compensation"] = {"enabled": False, "arithmetic_policy": "target_format_only"}
    original["kernel"]["task"] += (
        " The same source will be tested at FP64, FP32, FP16 and BF16. "
        "Keep each floating execution in its requested format. Failures are legitimate; "
        "never substitute FP32/FP64 for a failing lower precision, even if cast back. "
        "Wider precomputed constants may be cast before use; unused buffers are allowed. "
        "Do not change the recurrence, boundaries or workload. No prior Deriche sources are seeds."
    )
    cpu = copy.deepcopy(original)
    cpu["execution"] = {"mode": "local"}
    cpu["measure"]["backends"] = [
        {
            "type": "torch",
            "name": "cpu",
            "device": "cpu",
            "precisions": ["fp64", "fp32", "fp16", "bf16"],
            "precision_audit": "enforce",
        }
    ]
    cpu["compatibility"] = {"enabled": False}
    cpu["success"] = {"required_backends": [], "required_precisions": {}}
    cpu["runs_dir"] = str(OUTPUT / "cpu/runs/polybench-deriche")
    gpu = copy.deepcopy(original)
    gpu["execution"].update(call_timeout_s=120, pause_max_s=120)
    gpu["execution"]["resources"]["a100"]["workspace_root"] = (
        "/home/gbrun/lassi-x-work/terra-deriche-strict-rerun-20261016/mini"
    )
    gpu["measure"]["backends"][0].update(
        precision_audit="enforce", timeout_s=900, cuda_memory_limit_mb=8192
    )
    gpu["compatibility"] = {"enabled": True, "correction_rounds": 2}
    gpu["screening"] = {"enabled": False}
    gpu["runs_dir"] = str(OUTPUT / "gpu/runs/polybench-deriche")
    for name, config in (("cpu", cpu), ("gpu", gpu)):
        RunConfig.model_validate(config)
        path = OUTPUT / "configs" / f"{name}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(config, sort_keys=False))
    write_json(
        OUTPUT / "campaign.json",
        {
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
            "kernel": "polybench-deriche",
            "policy": "executed-dtype-v3",
            "precisions": ["fp64", "fp32", "fp16", "bf16"],
            "stages": ["fresh_cpu_translation", "mini_gpu_compatibility", "large_evaluation_only"],
            "numerical_repair": False,
            "old_sources_used_as_seeds": False,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )


def latest(folder: Path) -> Path:
    records = sorted(folder.glob("*/run.json"))
    if not records:
        raise RuntimeError(f"No completed record in {folder}")
    return records[-1]


def large_plan(record_path: Path) -> Path:
    plan = json.loads((FROZEN / "campaign.json").read_text())
    template = next(e for e in plan["entries"] if e["name"] == "polybench-deriche")
    config = yaml.safe_load(Path(template["config"]).read_text())
    config["models"] = yaml.safe_load((OUTPUT / "configs/gpu.yaml").read_text())["models"]
    config["compensation"] = {"enabled": False, "arithmetic_policy": "target_format_only"}
    config["compatibility"] = {"enabled": False}
    config["screening"] = {"enabled": False}
    config["execution"]["resources"]["a100"]["workspace_root"] = (
        "/home/gbrun/lassi-x-work/terra-deriche-strict-rerun-20261016/large"
    )
    config["measure"]["backends"][0]["precision_audit"] = "enforce"
    large = OUTPUT / "large"
    cfg = large / "configs/polybench-deriche.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(yaml.safe_dump(config, sort_keys=False))
    RunConfig.load(cfg)
    record = json.loads(record_path.read_text())
    mini_config = yaml.safe_load((OUTPUT / "configs/gpu.yaml").read_text())
    mini = read_profile(Path(mini_config["kernel"]["reference"]).with_suffix(".h"), "mini")
    # Frozen campaign reference header defines the approved LARGE dimensions.
    target = read_profile(Path(config["kernel"]["reference"]).with_suffix(".h"), "large")
    cells = []
    for base in record["candidates"]:
        if base["status"] != "ok":
            continue
        cid = base["candidate_id"]
        for precision in ("fp16", "bf16"):
            ports = [
                c
                for c in record.get("compatibility_candidates", [])
                if c.get("parent_candidate_id") == cid
                and c["status"] == "ok"
                and c.get("target_precision") == precision
            ]
            source = Path((ports[-1] if ports else base)["module_path"])
            module = large / "seeds/polybench-deriche" / f"{cid}-{precision}.py"
            module.parent.mkdir(parents=True, exist_ok=True)
            try:
                text, changes = specialize_source(
                    source.read_text(), "polybench-deriche", mini, target
                )
                error = None
            except (ValueError, SyntaxError) as exc:
                text, changes, error = source.read_text(), [], str(exc)
            module.write_text(text)
            cells.append(
                {
                    "candidate_id": cid,
                    "precision": precision,
                    "module": str(module),
                    "source": str(source),
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
                    "changes": changes,
                    "specialization_error": error,
                }
            )
    path = large / "campaign.json"
    write_json(
        path,
        {
            "entries": [
                {
                    "name": "polybench-deriche",
                    "config": str(cfg),
                    "cells": cells,
                    "references": template["references"],
                }
            ],
            "policy": "executed-dtype-v3",
            "models": [],
            "dataset": "large",
        },
    )
    return path


def run() -> int:
    state = {"pid": os.getpid(), "status": "starting", "started_at": datetime.now(UTC).isoformat()}

    def update(**kwargs):
        state.update(kwargs)
        write_json(OUTPUT / "status.json", state)

    def phase(name: str, command: list[str]) -> int:
        update(status="running", phase=name)
        print(subprocess.list2cmdline(command), flush=True)
        return subprocess.run(
            command,
            cwd=REPO,
            check=False,
            timeout=180 if name == "gpu_preflight" else None,
        ).returncode

    cli = str(REPO / ".venv/bin/lassi-x")
    try:
        code = phase(
            "fresh_cpu_translation",
            [cli, "run", str(OUTPUT / "configs/cpu.yaml"), "--until", "cpu-verified"],
        )
        cpu = latest(OUTPUT / "cpu/runs/polybench-deriche")
        result = json.loads(cpu.read_text())
        if model_service_interrupted(result):
            raise RuntimeError(f"Model quota/auth interruption saved at {cpu}")
        if code or result["status"] != "cpu_verified":
            raise RuntimeError(f"CPU generation produced no valid baseline: {cpu}")
        update(cpu_run=str(cpu.parent))
        code = phase(
            "gpu_preflight",
            [cli, "execution", "doctor", "--config", str(OUTPUT / "configs/gpu.yaml")],
        )
        if code:
            raise RuntimeError("A100 execution preflight failed; fresh CPU baseline retained")
        phase(
            "mini_gpu_compatibility",
            [
                cli,
                "run",
                str(OUTPUT / "configs/gpu.yaml"),
                "--from-cpu-baseline",
                str(cpu.parent / "cpu-baseline"),
            ],
        )
        gpu = latest(OUTPUT / "gpu/runs/polybench-deriche")
        result = json.loads(gpu.read_text())
        update(gpu_run=str(gpu.parent))
        if model_service_interrupted(result) or result.get("error"):
            raise RuntimeError(f"GPU stage interrupted; saved at {gpu}")
        # A nonzero GPU verdict can be a legitimate precision failure, not a reason
        # to discard the source or regenerate it. LARGE evaluation does not call models.
        plan = large_plan(gpu)
        code = phase(
            "large_evaluation_only",
            [
                str(REPO / ".venv/bin/python"),
                str(REPO / "experiments/repair-campaigns/run_gpu_repair_comparison.py"),
                "--output",
                str(plan.parent),
                "--resume",
                "--execute",
                "--baseline-only",
            ],
        )
        if code:
            raise RuntimeError(
                "LARGE evaluation interrupted; retain checkpoints and all MINI results"
            )
        update(status="completed", finished_at=datetime.now(UTC).isoformat())
        return 0
    except Exception as exc:
        update(status="interrupted", error=f"{type(exc).__name__}: {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
        return 0
    if args.detach:
        with (OUTPUT / "launcher.log").open("a") as log:
            proc = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve())],
                cwd=REPO,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        write_json(OUTPUT / "launcher.json", {"pid": proc.pid})
        print(f"Started fresh Terra Deriche queue PID {proc.pid}")
        return 0
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
