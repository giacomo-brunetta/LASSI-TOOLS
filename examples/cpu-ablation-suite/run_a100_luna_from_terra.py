"""Compare numerical repair models using the same Terra CPU baselines on A100."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lassi_x.artifacts import write_json
from lassi_x.compensation import select_weak_points
from lassi_x.config import RunConfig
from lassi_x.types import Measurement

REPO = Path(__file__).resolve().parents[2]
SOURCE_CAMPAIGN = REPO / "runs/a100-terra-medium-20261010"
CAMPAIGN = REPO / "runs/a100-luna-numerical-repair-20261013"


def make_plan(campaign: Path = CAMPAIGN, models: tuple[str, ...] = ("terra", "luna")) -> Path:
    if campaign.exists():
        raise FileExistsError(f"Refusing to overwrite campaign directory: {campaign}")
    source = json.loads((SOURCE_CAMPAIGN / "campaign.json").read_text())
    model_sets = {
        name: yaml.safe_load(
            (REPO / f"examples/cpu-ablation-suite/models/{name}.yaml").read_text()
        )["models"]
        for name in models
    }
    entries_by_model: dict[str, list[dict]] = {name: [] for name in models}
    for item in source["entries"]:
        baseline = Path(item["baseline"])
        if not (baseline / "manifest.json").is_file():
            raise FileNotFoundError(f"Terra CPU baseline missing: {baseline}")
        config = yaml.safe_load((SOURCE_CAMPAIGN / item["config"]).read_text())
        original_run = json.loads(
            next((SOURCE_CAMPAIGN / "runs" / item["name"]).glob("*/run.json")).read_text()
        )
        run_config = RunConfig.model_validate(config)
        baseline_measurements = [
            Measurement.from_dict(measurement)
            for measurement in original_run["measurements"]
            if measurement.get("backend") == "a100-cuda"
            and measurement.get("compensation") == "none"
        ]
        targets = select_weak_points(
            baseline_measurements,
            error_threshold=run_config.compensation.error_threshold,
            error_metric=run_config.pareto_error_metric,
            comparison_scope=run_config.compensation.comparison_scope,
        )
        if not targets:
            continue
        for model_name, model_set in model_sets.items():
            model_config = {
                **config,
                "models": {
                    "planner": model_set["planner"],
                    "candidates": model_set["candidates"],
                    "compensation": model_set["compensation"],
                    "compatibility": model_set["planner"],
                },
            }
            model_config["compensation"]["enabled"] = True
            # Focus on numerical variants; compiler/runtime compatibility
            # leaves are outside this experiment's scope.
            model_config.setdefault("compatibility", {})["enabled"] = False
            model_config["runs_dir"] = str(campaign / model_name / "runs" / item["name"])
            config_path = campaign / model_name / "configs" / f"{item['name']}.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(yaml.safe_dump(model_config, sort_keys=False))
            RunConfig.model_validate(model_config)
            entries_by_model[model_name].append(
                {
                    "name": item["name"],
                    "model": model_name,
                    "config": str(config_path),
                    "baseline": str(baseline),
                    "first_translation_model": "gpt-5.6-terra",
                    "numerical_repair_model": model_set["compensation"]["model"],
                    "numerical_repair_targets": [
                        {
                            "candidate_id": target.candidate_id,
                            "precision": target.precision,
                            "status": target.status.value,
                            "relative_l2": target.relative_l2,
                        }
                        for target in targets
                    ],
                }
            )
    campaign.mkdir(parents=True, exist_ok=True)
    write_json(
        campaign / "campaign.json",
        {
            "campaign": "terra-baseline-a100-numerical-repair",
            "created_at": datetime.now(UTC).isoformat(),
            "source_campaign": str(SOURCE_CAMPAIGN),
            "endpoint_id": source["endpoint_id"],
            "dataset": source["dataset"],
            "precisions": source["precisions"],
            "models": list(models),
            "entries": [entry for model in models for entry in entries_by_model[model]],
        },
    )
    write_json(
        campaign / "plan.json",
        {"entries": [entry for model in models for entry in entries_by_model[model]]},
    )
    return campaign / "plan.json"


def execute(plan: Path) -> int:
    entries = json.loads(plan.read_text())["entries"]
    state = {
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "completed": [],
        "total": len(entries),
        "current": None,
        "failures": [],
    }
    status_path = plan.parent / "status.json"

    def save() -> None:
        write_json(status_path, state)

    save()
    executable = REPO / ".venv/bin/lassi-x"
    for index, entry in enumerate(entries, 1):
        state["current"] = {"index": index, **entry}
        save()
        command = [
            str(executable),
            "--log-level",
            "ERROR",
            "run",
            entry["config"],
            "--from-cpu-baseline",
            entry["baseline"],
            "--allow-adaptations",
        ]
        print(
            f"[{index}/{len(entries)}] {entry['model'].title()} numerical repair {entry['name']}",
            flush=True,
        )
        result = subprocess.run(command, cwd=REPO, check=False)
        state["completed"].append({"name": entry["name"], "returncode": result.returncode})
        if result.returncode:
            state["failures"].append({"name": entry["name"], "returncode": result.returncode})
        save()
    state.update(
        status="finished_with_failures" if state["failures"] else "finished",
        finished_at=datetime.now(UTC).isoformat(),
        current=None,
    )
    save()
    return int(bool(state["failures"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-plan", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--detach", action="store_true")
    parser.add_argument(
        "--models", nargs="+", choices=["terra", "luna", "sol"], default=["terra", "luna"]
    )
    parser.add_argument("--output", type=Path, default=CAMPAIGN)
    args = parser.parse_args()
    if args.run_plan:
        return execute(args.run_plan.resolve())
    plan = make_plan(args.output.resolve(), tuple(args.models))
    if not args.detach:
        return execute(plan)
    log_path = plan.parent / "launcher.log"
    with log_path.open("x") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--run-plan", str(plan)],
            cwd=REPO,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print(f"Started A100 numerical repair launcher PID {process.pid}")
    print(f"Status: {plan.parent / 'status.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
