from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import time
from typing import TYPE_CHECKING, Any

from .arena import run_arena
from .artifacts import (
    append_jsonl,
    atomic_write,
    create_run_dir,
    write_json,
    write_resolved_config,
)
from .compensation import generate_compensation, select_weak_points
from .config import RunConfig
from .measurement import (
    build_backends,
    measure_compensation_variants,
    measure_variants,
)
from .pareto import frontier_indices
from .skills import AUTOMATION_SKILLS, install_root, require_automation_skills
from .types import Status
from .validation import build_oracle

if TYPE_CHECKING:
    from pathlib import Path


def _skill_records() -> list[dict[str, str]]:
    root = install_root()
    records = []
    for name in AUTOMATION_SKILLS:
        path = root / name / "SKILL.md"
        records.append(
            {
                "name": name,
                "version": "1.0.0",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return records


def _summary(record: dict[str, Any]) -> str:
    candidates = record["candidates"]
    measurements = record["measurements"]
    frontier = record["frontier"]
    lines = [
        f"# LASSI-X run: {record['kernel']}",
        "",
        f"- Status: **{record['status']}**",
        f"- Oracle: original C/C++ FP64 (`{record['oracle']['output_path']}`)",
        f"- Candidates generated: {len(candidates)}",
        f"- Candidates passing FP64 reference validation: "
        f"{sum(c['status'] == 'ok' for c in candidates)}",
        f"- Compensation variants: {len(record['compensation_variants'])}",
        f"- Measurements: {len(measurements)}",
        f"- Frontier points: {len(frontier)}",
        "",
        "## Candidates",
        "",
    ]
    for candidate in candidates:
        lines.append(
            f"- `{candidate['candidate_id']}`: {candidate['status']}; "
            f"model={candidate['provider'] or 'ambient'}:{candidate['model']}; "
            f"corrections={candidate['correction_rounds']}"
        )
    lines += ["", "## Frontier", ""]
    for point in frontier:
        lines.append(
            f"- `{point['candidate_id']}/{point['variant_id']}` "
            f"{point['backend']} {point['precision']} {point['compensation']}: "
            f"latency={point['latency_s']} s, max_rel_error={point['max_rel_error']}"
        )
    return "\n".join(lines) + "\n"


async def run_pipeline(config_path: Path) -> tuple[int, Path]:
    require_automation_skills()
    config = RunConfig.load(config_path)
    run_root = (
        config.runs_dir if config.runs_dir.is_absolute() else config.project.root / config.runs_dir
    )
    run_dir = create_run_dir(run_root, config.kernel.name)
    write_resolved_config(
        run_dir / "resolved-config.yaml",
        config.model_dump(mode="json"),
    )
    started_at = dt.datetime.now(dt.UTC).isoformat()
    started = time.perf_counter()
    try:
        oracle = await build_oracle(config, run_dir)
        candidates, planner_record = await run_arena(config, oracle, run_dir)
        valid_candidates = [candidate for candidate in candidates if candidate.status == Status.OK]
        backends = build_backends(config)
        base_variants = [
            (
                candidate.candidate_id,
                f"{candidate.candidate_id}-base",
                candidate.module_path,
                "none",
            )
            for candidate in valid_candidates
        ]
        base_measurements = await measure_variants(config, oracle, base_variants, backends)
        compensation_variants = []
        if config.compensation.enabled and valid_candidates:
            weak = select_weak_points(base_measurements)
            candidate_map = {candidate.candidate_id: candidate for candidate in valid_candidates}
            backend_map = {backend.name: backend for backend in config.measure.backends}
            compensation_variants = list(
                await asyncio.gather(
                    *(
                        generate_compensation(
                            config,
                            oracle,
                            run_dir,
                            candidate_map[point.candidate_id],
                            point,
                            backend_map[point.backend],
                        )
                        for point in weak
                    )
                )
            )
        valid_compensation = [
            variant for variant in compensation_variants if variant.status == Status.OK
        ]
        generated_specs = [
            (
                variant.candidate_id,
                variant.variant_id,
                variant.module_path,
                variant.technique,
            )
            for variant in valid_compensation
        ]
        generated_measurements = await measure_compensation_variants(
            config, oracle, generated_specs, backends
        )
        measurements = base_measurements + generated_measurements
        indices = frontier_indices(measurements)
        frontier = [measurements[index].to_dict() for index in indices]
        status = "ok" if frontier else "failed"
        for measurement in measurements:
            append_jsonl(run_dir / "measurements.jsonl", measurement.to_dict())
        write_json(run_dir / "frontier.json", frontier)
        record = {
            "schema_version": 1,
            "status": status,
            "kernel": config.kernel.name,
            "started_at": started_at,
            "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            "wall_seconds": round(time.perf_counter() - started, 3),
            "config_path": str(config_path.resolve()),
            "oracle": {
                "kind": "c_reference_fp64",
                "reference_path": str(config.resolve_project_path(config.kernel.reference)),
                "output_path": str(oracle.output_path),
                "numel": int(oracle.values.size),
            },
            "skills": _skill_records(),
            "planner": planner_record,
            "candidates": [candidate.to_dict() for candidate in candidates],
            "compensation_variants": [variant.to_dict() for variant in compensation_variants],
            "measurements": [measurement.to_dict() for measurement in measurements],
            "frontier": frontier,
        }
        write_json(run_dir / "run.json", record)
        atomic_write(run_dir / "summary.md", _summary(record))
        return (0 if frontier else 1), run_dir
    except Exception as exc:
        record = {
            "schema_version": 1,
            "status": "failed",
            "kernel": config.kernel.name,
            "started_at": started_at,
            "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            "wall_seconds": round(time.perf_counter() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }
        write_json(run_dir / "run.json", record)
        atomic_write(
            run_dir / "summary.md",
            f"# LASSI-X run: {config.kernel.name}\n\n"
            f"- Status: **failed**\n- Error: `{record['error']}`\n",
        )
        return 1, run_dir
