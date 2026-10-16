"""Evaluate all 33 kernels at LARGE on A100 without model or repair calls.

Select the best accepted MINI GPU source for each precision, specialize only
dataset dimensions/timestep bounds, and compare with a fresh independent LARGE
C oracle. Both valid measurements and size/compilation/numerical failures remain
in the output. Existing MINI artifacts are never modified.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import yaml

from lassi_x.artifacts import write_json
from lassi_x.config import RunConfig
from lassi_x.dataset_specialization import read_profile, specialize_source
from lassi_x.execution import ExecutionContext
from lassi_x.measurement import build_backends
from lassi_x.scheduler import PipelineScheduler
from lassi_x.validation import OracleResult, build_oracle

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "runs/a100-terra-medium-20261010"
DEFAULT_OUTPUT = REPO / "runs/a100-large-validation-20261014"
PRECISIONS = ("fp64", "fp32", "fp16", "bf16")
RESULT_SOURCES = (
    (SOURCE, "runs/*/*/run.json"),
    (REPO / "runs/a100-luna-from-terra-20261013", "runs/*/*/run.json"),
    (REPO / "runs/a100-luna-numerical-repair-20261013", "*/runs/*/*/run.json"),
    (REPO / "runs/a100-sol-numerical-repair-20261014", "sol/runs/*/*/run.json"),
)


def prepare(output: Path, refresh: bool = False) -> Path:
    if output.exists() and (not refresh or (output / "runs").exists()):
        raise FileExistsError(f"Refusing to overwrite campaign: {output}")
    manifest = json.loads((SOURCE / "campaign.json").read_text())
    candidates: dict[tuple[str, str], list[dict]] = {}
    for root, pattern in RESULT_SOURCES:
        for path in root.glob(pattern):
            record = json.loads(path.read_text())
            accepted = {
                item["module_path"]
                for field in (
                    "candidates",
                    "numerical_candidates",
                    "compatibility_candidates",
                    "compensation_variants",
                )
                for item in record.get(field, [])
                if item["status"] == "ok"
            }
            for point in record.get("measurements", []):
                if (
                    point["status"] == "ok"
                    and point.get("evaluation_semantic_verified")
                    and point.get("relative_l2") is not None
                    and point["module_path"] in accepted
                    and not (
                        point["precision"] != "fp64"
                        and point.get("observed_output_precision") in {"float64", "fp64"}
                    )
                ):
                    candidates.setdefault((record["kernel"], point["precision"]), []).append(point)
    entries = []
    # Begin with the small custom scientific LARGE profiles as an inexpensive smoke check.
    source_entries = sorted(manifest["entries"], key=lambda e: e["name"].startswith("polybench-"))
    for entry in source_entries:
        name = entry["name"]
        original = yaml.safe_load((SOURCE / entry["config"]).read_text())
        reference = Path(original["kernel"]["reference"])
        header = reference.with_suffix(".h")
        if not header.exists():
            header = reference.parent / "common.h"
        mini = read_profile(header, "mini")
        large = read_profile(header, "large")
        baseline = Path(entry["baseline"])
        base_manifest = json.loads((baseline / "manifest.json").read_text())
        fallback = baseline / base_manifest["candidates"][0]["module_path"]
        cells = []
        for precision in PRECISIONS:
            points = sorted(
                candidates.get((name + "-mini", precision), []),
                key=lambda point: (point["relative_l2"], point.get("latency_s") or float("inf")),
            )
            paths = list(
                dict.fromkeys([Path(point["module_path"]) for point in points] + [fallback])
            )
            errors = []
            for source in paths:
                try:
                    text, changes = specialize_source(source.read_text(), name, mini, large)
                except (ValueError, SyntaxError, OSError) as exc:
                    errors.append({"source": str(source), "error": str(exc)})
                    continue
                target = output / "modules" / name / f"candidate-{precision}.py"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
                cells.append(
                    {
                        "precision": precision,
                        "module": str(target),
                        "original_source": str(source),
                        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "specialization": changes,
                        "skipped_sources": errors,
                    }
                )
                break
            else:
                cells.append({"precision": precision, "specialization_errors": errors})
        config = original
        config["kernel"]["name"] = name + "-large"
        config["kernel"]["validation_dataset"] = "large"
        config["oracle"]["build"] = [
            "-DLARGE_DATASET" if value == "-DMINI_DATASET" else "-O2" if value == "-O0" else value
            for value in config["oracle"]["build"]
        ]
        config["oracle"]["timeout_s"] = 3600
        config["measure"]["evaluation_dataset"] = "large"
        config["measure"]["warmup"] = 3
        config["measure"]["iterations"] = 20
        config["compensation"]["enabled"] = False
        config.setdefault("compatibility", {})["enabled"] = False
        config.setdefault("screening", {})["enabled"] = False
        config["runs_dir"] = str(output / "runs" / name)
        for resource in config["execution"]["resources"].values():
            resource["workspace_root"] += f"/large-validation-20261014/{name}"
        for backend in config["measure"]["backends"]:
            backend["timeout_s"] = 900
        RunConfig.model_validate(config)
        config_path = output / "configs" / f"{name}.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.safe_dump(config, sort_keys=False))
        entries.append(
            {
                "name": name,
                "config": str(config_path),
                "mini_profile": mini,
                "large_profile": large,
                "profile_header": str(header),
                "cells": cells,
            }
        )
    plan = output / "campaign.json"
    write_json(
        plan,
        {
            "dataset": "large",
            "model_calls": False,
            "source_campaign": str(SOURCE),
            "candidate_selection": "lowest accepted MINI relative_l2 per precision",
            "entries": entries,
        },
    )
    return plan


async def execute(plan: Path) -> int:
    campaign = plan.parent
    entries = json.loads(plan.read_text())["entries"]
    state = {
        "status": "running",
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "completed": [],
        "total": len(entries),
        "current": None,
    }
    status_path = campaign / "status.json"
    write_json(status_path, state)
    for entry in entries:
        name = entry["name"]
        run_dir = campaign / "runs" / name
        record_path = run_dir / "run.json"
        previous = None
        if record_path.exists():
            previous = json.loads(record_path.read_text())
            if previous.get("status") in {"complete", "reference_failed"}:
                state["completed"].append({"name": name, "status": previous["status"]})
                continue
        run_dir.mkdir(parents=True, exist_ok=True)
        config = RunConfig.load(Path(entry["config"]))
        state["current"] = {"kernel": name, "phase": "build_large_c_oracle"}
        write_json(status_path, state)
        record = previous or {
            "kernel": name,
            "dataset": "large",
            "status": "running",
            "large_profile": entry["large_profile"],
            "measurements": [],
            "cells": entry["cells"],
        }
        record["status"] = "running"
        record.pop("error", None)
        try:
            cached = record.get("oracle")
            if cached and Path(cached["path"]).is_file():
                path = Path(cached["path"])
                if hashlib.sha256(path.read_bytes()).hexdigest() != cached["output_sha256"]:
                    raise ValueError("cached LARGE oracle checksum mismatch")
                oracle = OracleResult(
                    path,
                    np.load(path),
                    source_sha256=cached["source_sha256"],
                    determinism_runs=cached["determinism_runs"],
                )
            else:
                oracle = await build_oracle(config, run_dir)
            np.save(run_dir / "oracle/reference.npy", oracle.values)
            path = run_dir / "oracle/reference.npy"
            oracle = OracleResult(
                path,
                oracle.values,
                source_sha256=oracle.source_sha256,
                output_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                determinism_runs=oracle.determinism_runs,
            )
            record["oracle"] = {
                "path": str(path),
                "numel": int(oracle.values.size),
                "determinism_runs": oracle.determinism_runs,
                "source_sha256": oracle.source_sha256,
                "output_sha256": oracle.output_sha256,
            }
            write_json(record_path, record)
        except Exception as exc:
            record.update(status="reference_failed", error=f"{type(exc).__name__}: {exc}")
            write_json(record_path, record)
            state["completed"].append({"name": name, "status": record["status"]})
            write_json(status_path, state)
            continue
        try:
            async with await ExecutionContext.start(config, run_dir) as execution:
                scheduler = PipelineScheduler(config.scheduler)
                backend = build_backends(config, execution, scheduler)[0]
                for cell in entry["cells"]:
                    precision = cell["precision"]
                    if any(m["precision"] == precision for m in record["measurements"]):
                        continue
                    state["current"] = {
                        "kernel": name,
                        "phase": "gpu_validation_and_timing",
                        "precision": precision,
                    }
                    write_json(status_path, state)
                    if "module" not in cell:
                        record["measurements"].append(
                            {"precision": precision, "status": "specialization_failed"}
                        )
                    else:
                        execution.require_live_resources()
                        point = await backend.measure(
                            config,
                            oracle,
                            Path(cell["module"]),
                            candidate_id="large",
                            variant_id=f"large-{precision}",
                            precision=precision,
                            compensation="inherited-mini-source",
                        )
                        record["measurements"].append(point.to_dict())
                    write_json(record_path, record)
        except Exception as exc:
            record.update(status="interrupted", error=f"{type(exc).__name__}: {exc}")
            write_json(record_path, record)
            state.update(status="interrupted", error=record["error"])
            write_json(status_path, state)
            return 1
        record.update(status="complete", finished_at=datetime.now(UTC).isoformat())
        record["numerically_stable_precisions"] = [
            measurement["precision"] for measurement in record["measurements"]
            if measurement["status"] == "ok"
            and measurement.get("relative_l2") is not None
            and measurement["relative_l2"] <= config.accuracy.concerning_relative_l2
        ]
        write_json(record_path, record)
        state["completed"].append({"name": name, "status": record["status"]})
        write_json(status_path, state)
    state.update(status="finished", current=None, finished_at=datetime.now(UTC).isoformat())
    write_json(status_path, state)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--run-plan", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--refresh-prepared", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.run_plan:
        return asyncio.run(execute(args.run_plan.resolve()))
    plan = (
        args.output.resolve() / "campaign.json"
        if args.resume
        else prepare(args.output.resolve(), refresh=args.refresh_prepared)
    )
    print(f"Prepared LARGE validation for 33 kernels: {plan}")
    if not args.execute:
        return 0
    if not args.detach:
        return asyncio.run(execute(plan))
    with (plan.parent / "launcher.log").open("a" if args.resume else "x") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--run-plan", str(plan)],
            cwd=REPO,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print(f"Started LARGE validation PID {process.pid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
