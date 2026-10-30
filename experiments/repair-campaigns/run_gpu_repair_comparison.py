"""Validate frozen LARGE Terra GPU ports, then independently repair Luna/Terra/SOL.

No translation, planner, seed adaptation agent, or compatibility agent is called.
Infrastructure failures halt the queue rather than becoming scientific outcomes.
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
from lassi_x.compensation import generate_compensation
from lassi_x.config import RunConfig
from lassi_x.dataset_specialization import read_profile, specialize_source
from lassi_x.execution.context import ExecutionContext
from lassi_x.interruptions import model_service_interrupted
from lassi_x.measurement import build_backends
from lassi_x.scheduler import PipelineScheduler
from lassi_x.skills import require_automation_skills
from lassi_x.types import Candidate, Measurement, Status
from lassi_x.validation import OracleResult, build_oracle

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "runs/a100-large-clean-restart-20261015"
TERRA = REPO / "runs/a100-terra-medium-20261010"
ARCHIVE = REPO / "runs/legacy/unconstrained-precision-20261015/a100-large-repair-20261015"
DEFAULT = REPO / "runs/a100-clean-gpu-repairs-20261016"
MODELS = ("luna", "terra", "sol")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output: Path) -> Path:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    inventory = json.loads((FROZEN / "baseline-inventory.json").read_text())
    entries = []
    for kernel in sorted({e["kernel"] for e in inventory["entries"]}):
        bases = [e for e in inventory["entries"] if e["kernel"] == kernel]
        records = sorted((TERRA / "runs" / kernel).glob("*/run.json"))
        record = json.loads(records[-1].read_text())
        base_by_id = {c["candidate_id"]: c for c in record["candidates"]}
        reference_dir = FROZEN / "references" / kernel
        # Only frozen workload/configuration is reused from the quarantined campaign.
        # No old candidate edits, measurements, or numerical traces are imported.
        text = (ARCHIVE / "luna/configs" / f"{kernel}.yaml").read_text()
        text = text.replace(
            str(REPO / "runs/a100-large-repair-20261015/references"), str(FROZEN / "references")
        )
        cfg = yaml.safe_load(text)
        cfg["arena"].pop("seed_sources", None)
        cfg["compensation"].update(
            enabled=True,
            arithmetic_policy="target_format_only",
            repair_catastrophic=True,
            correction_rounds=2,
        )
        cfg["compatibility"]["enabled"] = False
        cfg["kernel"]["task"] = (
            "Repair only the supplied, already translated Terra GPU implementation. "
            "Preserve the frozen LARGE workload, initialization and supplied-input semantics. "
            "Do not reduce sizes, iterations or output coverage. Explicit FP32/FP64 work in "
            "low-precision forward is forbidden and runtime tensor dtypes are audited. "
            "Do not reconstruct supplied inputs in forward. No earlier repairs are available."
        )
        cfg["scheduler"].update(max_candidate_flows=1, max_model_sessions=1)
        cfg["measure"].update(warmup=3, iterations=20)
        cfg["execution"].update(call_timeout_s=120, pause_max_s=120)
        cfg["execution"]["resources"]["a100"]["workspace_root"] = (
            "/home/gbrun/lassi-x-work/" + output.name + "/" + kernel
        )
        for backend in cfg["measure"]["backends"]:
            backend.update(precision_audit="report", timeout_s=900, cuda_memory_limit_mb=8192)
        original = yaml.safe_load((TERRA / "configs" / f"{kernel}.yaml").read_text())
        header = Path(original["kernel"]["reference"]).with_suffix(".h")
        if not header.exists():
            header = header.parent / "common.h"
        mini = read_profile(header, "mini")
        cells = []
        for base in bases:
            cid = base["candidate_id"]
            for precision in ("fp16", "bf16"):
                eligible = [
                    c
                    for c in record.get("compatibility_candidates", [])
                    if c.get("parent_candidate_id") == cid
                    and c["status"] == "ok"
                    and c.get("target_precision") == precision
                ]
                chosen = eligible[-1] if eligible else base_by_id[cid]
                source = Path(chosen["module_path"])
                module = output / "seeds" / kernel / f"{cid}-{precision}.py"
                module.parent.mkdir(parents=True, exist_ok=True)
                try:
                    adapted, changes = specialize_source(
                        source.read_text(), kernel, mini, base["frozen_dimensions"]
                    )
                    error = None
                except (ValueError, SyntaxError) as exc:
                    adapted, changes, error = source.read_text(), [], str(exc)
                module.write_text(adapted)
                cells.append(
                    {
                        "candidate_id": cid,
                        "precision": precision,
                        "module": str(module),
                        "source": str(source),
                        "source_sha256": digest(source),
                        "sha256": digest(module),
                        "changes": changes,
                        "specialization_error": error,
                        "source_kind": "terra_gpu_compatibility" if eligible else "terra_base",
                    }
                )
        config_path = output / "configs" / f"{kernel}.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        RunConfig.load(config_path)
        entries.append(
            {
                "name": kernel,
                "config": str(config_path),
                "cells": cells,
                "references": {str(p): digest(p) for p in reference_dir.iterdir()},
            }
        )
    plan = output / "campaign.json"
    write_json(
        plan,
        {
            "created_at": datetime.now(UTC).isoformat(),
            "models": list(MODELS),
            "dataset": "large",
            "entries": entries,
            "arithmetic_policy": "target_format_only",
            "weak_relative_l2_threshold": 0.01,
            "source_policy": (
                "Original Terra GPU bases or precision-specific compatibility ports; "
                "never numerical repairs"
            ),
        },
    )
    return plan


def oracle_from(path: Path) -> OracleResult:
    return OracleResult(path, np.load(path), output_sha256=digest(path))


def classification(measurements: list[dict], audit: dict) -> str:
    high = measurements[0]
    if high["status"] != "ok" or high.get("notes"):
        return "semantic_or_large_port_failure"
    low = measurements[-1]
    if low.get("precision_verdict") == "failed" or low.get("failure_kind") == "precision_policy":
        return "invalid_precision_promotion"
    if low.get("failure_kind") == "infrastructure_timeout":
        raise RuntimeError("A100 execution agent unreachable")
    if low["status"] in {"crashed", "timeout", "no_fit", "unsupported"}:
        return "compatibility_or_resource_failure"
    if not Measurement.from_dict(low).precision_eligible:
        return "precision_unverified"
    if low["status"] == "diverged" or low.get("relative_l2") is None or low["relative_l2"] > 0.01:
        return "numerical_repair"
    return "stable"


def baseline_record_path(output: Path, kernel: str, cell: dict) -> Path:
    return (
        output / "baseline-policy-v3" / kernel / f"{cell['candidate_id']}-{cell['precision']}.json"
    )


def cached_controls(record: dict, cell: dict) -> dict[str, dict]:
    """Reuse only matching source/profile controls, never certify old low-format data."""
    if record.get("cell", {}).get("sha256") != cell["sha256"]:
        return {}
    return {
        m["precision"]: m
        for m in record.get("measurements", [])
        if m["precision"] in {"fp64", "fp32"}
        and m.get("source_hash") == cell["sha256"]
        and m.get("source_integrity_verified")
        and m.get("evaluation_dataset") == "large"
        and (
            m["precision"] == "fp64"
            or (
                m.get("precision_verdict") == "passed"
                and m.get("precision_audit_protocol") == "executed-dtype-v3"
                and m.get("precision_audit_source_hash") == cell["sha256"]
            )
        )
    }


async def execute(plan_path: Path, *, baseline_only: bool = False) -> int:
    require_automation_skills()
    plan = json.loads(plan_path.read_text())
    output = plan_path.parent
    source_review_path = output / "terra-full-source-policy-audit.json"
    excluded = (
        {
            (e["kernel"], e["candidate"], e["precision"]): e["sha256"]
            for e in json.loads(source_review_path.read_text())["entries"]
            if e["classification"] == "invalid_precision_promotion"
        }
        if source_review_path.exists()
        else {}
    )
    state = {
        "status": "baseline_validation",
        "pid": os.getpid(),
        "completed_cells": 0,
        "total_cells": sum(len(e["cells"]) for e in plan["entries"]),
    }
    status_path = output / "status.json"

    def update(**kw):
        state.update(kw)
        write_json(status_path, state)

    update()
    try:
        for entry in plan["entries"]:
            kernel = entry["name"]
            cfg = RunConfig.load(Path(entry["config"]))
            for filename, expected in entry["references"].items():
                if digest(Path(filename)) != expected:
                    raise ValueError(f"Frozen reference changed: {filename}")
            run_dir = output / "baseline" / kernel
            run_dir.mkdir(parents=True, exist_ok=True)
            update(current={"kernel": kernel, "phase": "oracle"})
            oracle_path = run_dir / "oracle/reference.npy"
            if oracle_path.exists():
                oracle = oracle_from(oracle_path)
            else:
                built = await build_oracle(cfg, run_dir)
                np.save(oracle_path, built.values)
                oracle = oracle_from(oracle_path)
            async with await ExecutionContext.start(cfg, run_dir) as ctx:
                reports = await asyncio.wait_for(ctx.handshakes(), 120)
                if not any(a.kind == "cuda" for r in reports.values() for a in r.accelerators):
                    raise RuntimeError("No CUDA accelerator at A100 endpoint")
                backend = build_backends(cfg, ctx, PipelineScheduler(cfg.scheduler))[0]
                for cell in entry["cells"]:
                    cid, precision = cell["candidate_id"], cell["precision"]
                    result_path = baseline_record_path(output, kernel, cell)
                    if digest(Path(cell["module"])) != cell["sha256"]:
                        raise ValueError("Frozen GPU seed changed")
                    if result_path.exists() and (
                        json.loads(result_path.read_text()).get("cell", {}).get("sha256")
                        == cell["sha256"]
                    ):
                        state["completed_cells"] += 1
                        continue
                    old_path = run_dir / f"{cid}-{precision}.json"
                    old = json.loads(old_path.read_text()) if old_path.exists() else {}
                    if excluded.get((kernel, cid, precision)) == cell["sha256"]:
                        write_json(
                            result_path,
                            {
                                "classification": "invalid_precision_promotion",
                                "cell": cell,
                                "measurements": old.get("measurements", []),
                                "evidence": str(source_review_path),
                                "original_record": str(old_path),
                                "baseline_policy_version": "v3",
                            },
                        )
                        state["completed_cells"] += 1
                        continue
                    if cell["specialization_error"]:
                        write_json(
                            result_path,
                            {
                                "classification": "size_specialization_failure",
                                "cell": cell,
                                "measurements": [],
                            },
                        )
                        state["completed_cells"] += 1
                        continue
                    points = []
                    controls = cached_controls(old, cell)
                    for p in ("fp64", "fp32", precision):
                        update(
                            current={
                                "kernel": kernel,
                                "candidate": cid,
                                "precision": p,
                                "source_precision": precision,
                            }
                        )
                        measured = (
                            Measurement.from_dict(controls[p])
                            if p in controls
                            else await backend.measure(
                                cfg,
                                oracle,
                                Path(cell["module"]),
                                candidate_id=cid,
                                variant_id=f"base-{cid}-{precision}-{p}",
                                precision=p,
                                compensation="unrepaired-terra-gpu",
                            )
                        )
                        points.append(measured.to_dict())
                        if measured.failure_kind == "infrastructure_timeout":
                            raise RuntimeError(measured.notes)
                        if p == "fp64" and (measured.status != Status.OK or measured.notes):
                            break
                    audit_path = (
                        Path(cell["module"]).parent
                        / f"base-{cid}-{precision}-{precision}-{precision}-dtype-audit.json"
                    )
                    audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
                    write_json(
                        result_path,
                        {
                            "cell": cell,
                            "measurements": points,
                            "dtype_audit": audit,
                            "classification": classification(points, audit),
                            "baseline_policy_version": "v3",
                            "original_record": str(old_path) if old_path.exists() else None,
                            "reused_control_precisions": list(controls),
                        },
                    )
                    state["completed_cells"] += 1
                    update()
        targets = []
        summary = {}
        for entry in plan["entries"]:
            for cell in entry["cells"]:
                p = baseline_record_path(output, entry["name"], cell)
                record = json.loads(p.read_text())
                reason = record["classification"]
                summary[reason] = summary.get(reason, 0) + 1
                if reason == "numerical_repair":
                    targets.append(
                        {
                            "kernel": entry["name"],
                            "baseline_record": str(p),
                            "config": entry["config"],
                            **cell,
                        }
                    )
        write_json(output / "repair-candidates.json", {"summary": summary, "targets": targets})
        if baseline_only:
            update(
                status="baseline_completed", baseline_summary=summary, repair_targets=len(targets)
            )
            return 0
        update(status="repairs", baseline_summary=summary, repair_targets=len(targets))
        for model in MODELS:
            for index, target in enumerate(targets):
                kernel, cid, precision = (
                    target["kernel"],
                    target["candidate_id"],
                    target["precision"],
                )
                run_dir = output / model / kernel / f"{cid}-{precision}"
                result_path = run_dir / "repair.json"
                if result_path.exists():
                    saved = json.loads(result_path.read_text())
                    if saved.get("precision_policy_version") != "v3":
                        raise RuntimeError(
                            f"Preserved repair needs evaluation-only revalidation: {result_path}"
                        )
                    if saved["variant"]["status"] != "crashed":
                        continue
                    raise RuntimeError(
                        f"Interrupted repair requires explicit resume: {result_path}"
                    )
                run_dir.mkdir(parents=True, exist_ok=True)
                update(
                    current={
                        "model": model,
                        "kernel": kernel,
                        "candidate": cid,
                        "precision": precision,
                        "target_index": index + 1,
                    }
                )
                data = yaml.safe_load(Path(target["config"]).read_text())
                data["models"] = yaml.safe_load(
                    (REPO / f"experiments/cpu-generation/models/{model}.yaml").read_text()
                )["models"]
                for b in data["measure"]["backends"]:
                    b["precision_audit"] = "enforce"
                    b["precision_audit_reference"] = target["module"]
                data["execution"]["resources"]["a100"]["workspace_root"] += (
                    f"/{model}/{cid}-{precision}"
                )
                cfg = RunConfig.model_validate(data)
                baseline = json.loads(Path(target["baseline_record"]).read_text())
                point = Measurement.from_dict(baseline["measurements"][-1])
                if not point.precision_eligible:
                    raise RuntimeError("Baseline requires measurement-only precision revalidation")
                base = Candidate(
                    cid,
                    "gpt-5.6-terra",
                    "openai-codex",
                    "frozen original GPU port",
                    Path(target["module"]),
                    status=Status.OK,
                )
                oracle = oracle_from(output / "baseline" / kernel / "oracle/reference.npy")
                async with await ExecutionContext.start(cfg, run_dir) as ctx:
                    backends = build_backends(cfg, ctx, PipelineScheduler(cfg.scheduler))
                    variant = await generate_compensation(
                        cfg,
                        oracle,
                        run_dir,
                        ctx,
                        base,
                        [point],
                        cfg.measure.backends,
                        {b.spec.name: b for b in backends},
                    )
                accepted = (
                    variant.status == Status.OK
                    and bool(variant.target_measurements)
                    and all(p.stable_success for p in variant.target_measurements)
                )
                write_json(
                    result_path,
                    {
                        "variant": variant.to_dict(),
                        "stable_success": accepted,
                        "precision_policy_version": "v3",
                        "baseline_record": target["baseline_record"],
                    },
                )
                if model_service_interrupted(json.loads(result_path.read_text())):
                    raise RuntimeError(f"Model service interrupted: {result_path}")
        update(status="completed", current=None, finished_at=datetime.now(UTC).isoformat())
        return 0
    except Exception as exc:
        update(status="interrupted", error=f"{type(exc).__name__}: {exc}")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--baseline-only", action="store_true", help="No model or repair calls")
    args = parser.parse_args()
    output = args.output.resolve()
    plan = output / "campaign.json" if args.resume else prepare(output)
    print(plan)
    if not args.execute:
        return 0
    if args.detach:
        with (output / "launcher.log").open("a") as log:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--output",
                    str(output),
                    "--resume",
                    "--execute",
                    *(["--baseline-only"] if args.baseline_only else []),
                ],
                cwd=REPO,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Started clean GPU baseline/repair queue PID {proc.pid}")
        return 0
    return asyncio.run(execute(plan, baseline_only=args.baseline_only))


if __name__ == "__main__":
    raise SystemExit(main())
