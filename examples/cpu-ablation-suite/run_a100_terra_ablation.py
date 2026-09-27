"""Run A100 accelerator ablations from Terra CPU baselines, first with Luna then Terra.

The imported CPU candidates stay identical at the start of both model passes. The
selected model is used only for target-specific compatibility repair; portable
compensation remains disabled to keep the ablation focused.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lassi_x.config import RunConfig

REPO = Path(__file__).resolve().parents[2]
TERRA_RUNS = REPO / "runs/cpu-model-comparison-medium-20260916/terra/runs"
CAMPAIGN = REPO / "runs/a100-terra-cpu-baseline-ablation-20260924-rerun"
ENDPOINT_ID = "b162a840-38b4-4c1a-84cc-579fb62f4dfc"


def passing_runs() -> list[tuple[str, Path, Path]]:
    found: list[tuple[str, Path, Path]] = []
    for kernel_dir in sorted(path for path in TERRA_RUNS.iterdir() if path.is_dir()):
        records = sorted(kernel_dir.glob("*/run.json"))
        verified = []
        for record in records:
            data = json.loads(record.read_text())
            baseline = record.parent / "cpu-baseline"
            if data.get("status") == "cpu_verified" and (baseline / "manifest.json").is_file():
                verified.append((record, baseline, data))
        if not verified:
            continue
        record, baseline, data = verified[-1]
        manifest = json.loads((baseline / "manifest.json").read_text())
        if not manifest.get("candidates"):
            continue
        if any(item.get("status") != "ok" for item in manifest["candidates"]):
            raise ValueError(f"CPU baseline contains a non-passing candidate: {baseline}")
        found.append((kernel_dir.name, record.parent, baseline))
    return found


def model_settings(name: str) -> dict:
    path = REPO / f"examples/cpu-ablation-suite/models/{name}.yaml"
    models = yaml.safe_load(path.read_text())["models"]
    return models


def build_config(kernel: str, cpu_run: Path, baseline: Path, model: str) -> Path:
    config = yaml.safe_load((cpu_run / "resolved-config.yaml").read_text())
    model_set = model_settings(model)
    config["models"] = {
        "planner": model_set["planner"],
        "candidates": model_set["candidates"],
        "compensation": model_set["compensation"],
        "compatibility": model_set["planner"],
    }
    config["execution"] = {
        "mode": "academy",
        "exchange_url": "https://exchange.academy-agents.org",
        "auth": "globus",
        "default_resource": "a100",
        "resources": {
            "a100": {
                "endpoint_id": ENDPOINT_ID,
                "workspace_root": "/home/gbrun/lassi-x-work",
                "labels": ["cuda", "a100"],
            }
        },
        "mcp_timeout_s": 900,
        "call_timeout_s": 300,
        "dead_after_timeouts": 2,
        "heartbeat_interval_s": 15,
        "heartbeat_misses": 20,
        "pause_max_s": 900,
    }
    precisions = ["fp64", "fp32", "fp16", "bf16"]
    config["measure"]["precisions"] = precisions
    config["measure"]["backends"] = [
        {
            "type": "torch",
            "name": "a100-cuda",
            "device": "cuda",
            "resource": "a100",
            "precisions": precisions,
            "timeout_s": 600,
            "submit_timeout_s": 300,
        }
    ]
    config["measure"]["warmup"] = 3
    config["measure"]["iterations"] = 20
    config["measure"]["strict_precisions"] = ["fp64", "fp32"]
    config["success"] = {
        "required_backends": ["a100-cuda"],
        "required_precisions": {"a100-cuda": precisions},
    }
    config["runs_dir"] = str(CAMPAIGN / model / "runs" / kernel)
    # Keep this an accelerator repair-model ablation. Both passes start from
    # checksummed Terra candidates; no portable precision variants are added.
    config["compensation"]["enabled"] = False
    target = CAMPAIGN / model / "configs" / f"{kernel}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    RunConfig.model_validate(config)
    return target


def make_plan() -> Path:
    if CAMPAIGN.exists():
        raise FileExistsError(f"Refusing to overwrite campaign directory: {CAMPAIGN}")
    runs = passing_runs()
    if not runs:
        raise RuntimeError(f"No passing Terra CPU baselines found under {TERRA_RUNS}")
    entries = []
    # Model order is intentional: complete the Luna ablation before Terra.
    for model in ("luna", "terra"):
        for kernel, cpu_run, baseline in runs:
            config = build_config(kernel, cpu_run, baseline, model)
            entries.append(
                {
                    "model": model,
                    "kernel": kernel,
                    "cpu_run": str(cpu_run),
                    "baseline": str(baseline),
                    "config": str(config),
                }
            )
    CAMPAIGN.mkdir(parents=True, exist_ok=True)
    plan = CAMPAIGN / "plan.json"
    plan.write_text(json.dumps({"entries": entries}, indent=2) + "\n")
    print(f"Prepared {len(runs)} Terra CPU baselines and {len(entries)} A100 runs")
    print(f"Plan: {plan}")
    return plan


def execute(plan: Path) -> int:
    data = json.loads(plan.read_text())
    state = {
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "completed": 0,
        "total": len(data["entries"]),
        "current": None,
        "failures": [],
    }
    status_path = plan.parent / "status.json"

    def save() -> None:
        status_path.write_text(json.dumps(state, indent=2) + "\n")

    save()
    executable = REPO / ".venv/bin/lassi-x"
    failures = 0
    for index, entry in enumerate(data["entries"], 1):
        state["current"] = {"index": index, **entry}
        save()
        command = [
            str(executable),
            "run",
            entry["config"],
            "--from-cpu-baseline",
            entry["baseline"],
            "--allow-adaptations",
        ]
        print(f"[{index}/{len(data['entries'])}] {entry['model']} {entry['kernel']}", flush=True)
        result = subprocess.run(command, cwd=REPO, check=False)
        state["completed"] = index
        if result.returncode:
            failures += 1
            state["failures"].append(
                {"model": entry["model"], "kernel": entry["kernel"], "returncode": result.returncode}
            )
        save()
    state["status"] = "finished_with_failures" if failures else "finished"
    state["current"] = None
    save()
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run all prepared accelerator jobs")
    parser.add_argument("--detach", action="store_true", help="Run in the background and log output")
    parser.add_argument("--run-plan", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.run_plan:
        return execute(args.run_plan.resolve())
    plan = make_plan()
    if not args.execute:
        return 0
    if not args.detach:
        return execute(plan)
    log_path = CAMPAIGN / "launcher.log"
    with log_path.open("x") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--run-plan", str(plan)],
            cwd=REPO,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print(f"Started A100 ablation launcher PID {process.pid}; log: {log_path}")
    print(f"Status: {CAMPAIGN / 'status.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
