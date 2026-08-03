from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
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
from .compensation import CompensationVariant, generate_compensation, select_weak_points
from .config import RunConfig
from .execution import ExecutionContext
from .measurement import (
    build_backends,
    measure_compensation_variants,
    measure_variants,
)
from .pareto import frontier_indices
from .skills import AUTOMATION_SKILLS, install_root, require_automation_skills
from .types import Diagnostic, Measurement, Status
from .validation import build_oracle

if TYPE_CHECKING:
    from pathlib import Path


def _skill_records() -> list[dict[str, str]]:
    """Fingerprint the installed automation skills used by a run.

    Returns:
        One auditable record per required skill containing its name, declared
        version, and SHA-256 digest.

    Raises:
        OSError: If an installed skill file cannot be read.

    """
    root = install_root()
    manifest_path = root / ".lassi-x-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    bundle_version = str(manifest.get("lassi_x_version") or "unknown")
    records = []
    for name in AUTOMATION_SKILLS:
        path = root / name / "SKILL.md"
        records.append(
            {
                "name": name,
                "version": bundle_version,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return records


def _summary(record: dict[str, Any]) -> str:
    """Render a concise Markdown summary from a completed run record.

    Args:
        record: Final run artifact containing candidates, measurements, compensation
            variants, and Pareto-frontier points.

    Returns:
        Human-readable Markdown ending with a newline.

    """
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


def _reject_non_improving_variants(
    config: RunConfig,
    variants: list[CompensationVariant],
    base_measurements: list[Measurement],
    generated_measurements: list[Measurement],
) -> None:
    """Reject validated compensation that does not improve its targeted error.

    Args:
        config: Run configuration selecting the compensation error metric.
        variants: Validated compensation records to update in place.
        base_measurements: Measurements that motivated compensation.
        generated_measurements: Targeted measurements of validated variants.

    """
    base_by_cell = {
        (point.candidate_id, point.backend, point.precision): point for point in base_measurements
    }
    generated_by_cell = {
        (point.variant_id, point.backend, point.precision): point
        for point in generated_measurements
    }
    metric = config.compensation.error_metric
    for variant in variants:
        if variant.status != Status.OK:
            continue
        base = base_by_cell.get((variant.candidate_id, variant.backend, variant.precision))
        generated = generated_by_cell.get((variant.variant_id, variant.backend, variant.precision))
        if base is None or generated is None or generated.status != Status.OK:
            continue
        base_error = getattr(base, metric)
        generated_error = getattr(generated, metric)
        if base_error is None or generated_error is None or generated_error < base_error:
            continue
        message = (
            f"compensation did not improve targeted {metric}: "
            f"base={base_error:.8e}, variant={generated_error:.8e}"
        )
        variant.status = Status.REJECTED
        variant.diagnostics.append(Diagnostic(gate="compensation-effect", message=message))
        generated.status = Status.REJECTED
        generated.notes = f"{generated.notes}; {message}".strip("; ")


async def run_pipeline(config_path: Path) -> tuple[int, Path]:
    """Execute the complete translation, correction, and measurement pipeline.

    The function is the top-level orchestration state machine. It creates one immutable
    run directory, builds the authoritative C/C++ oracle, executes the configured candidate
    arena, measures accepted candidates, compensates weak FP16/BF16 points, constructs
    the Pareto frontier, and persists an auditable final record. Exceptions raised after
    run-directory creation are converted into failure artifacts.

    Args:
        config_path: YAML configuration defining the project, models, validation,
            measurement backends, and compensation policy.

    Returns:
        A pair containing a process-style exit code and the immutable run directory.
        The exit code is zero only when the run produces at least one frontier point.

    Raises:
        RuntimeError: If required Hermes automation skills are not installed.
        OSError: If configuration or initial run-directory artifacts cannot be read or
            created before protected execution begins.
        ValueError: If the configuration is invalid.

    """
    # Establish prerequisites and immutable run identity before executing any agent work.
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
        # Phase 0: start execution backends and the MCP server, and pin one workspace
        # toolset per agent role in the Hermes configuration for the duration of the run.
        async with await ExecutionContext.start(config, run_dir) as execution:
            return await _run_stages(config, config_path, run_dir, execution, started_at, started)
    except Exception as exc:
        # Preserve a terminal failure artifact once a run directory exists; callers can
        # distinguish execution failure from configuration or initialization failure.
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


async def _run_stages(
    config: RunConfig,
    config_path: Path,
    run_dir: Path,
    execution: ExecutionContext,
    started_at: str,
    started: float,
) -> tuple[int, Path]:
    """Run every pipeline stage inside a live execution context.

    Args:
        config: Validated run configuration.
        config_path: Original configuration path recorded for provenance.
        run_dir: Immutable run directory.
        execution: Running execution context serving agent tool calls.
        started_at: ISO timestamp of run start for the final record.
        started: Monotonic start time for wall-clock accounting.

    Returns:
        A pair containing a process-style exit code and the run directory.

    """
    # Phase 1: build the independent semantic oracle from the original C/C++ source.
    oracle = await build_oracle(config, run_dir)

    # Phase 2: plan the configured strategy count, generate candidates concurrently, and repair
    # each candidate until it passes FP64 validation or exhausts its correction budget.
    candidates, planner_record = await run_arena(config, oracle, run_dir, execution)
    valid_candidates = [candidate for candidate in candidates if candidate.status == Status.OK]

    # Phase 3: measure every accepted base candidate across configured backend and
    # precision cells before selecting any low-precision intervention.
    backends = build_backends(config, execution)
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

    # Phase 4: identify weak FP16/BF16 cells and generate their compensation variants
    # concurrently. Each variant runs its own sequential validation/repair loop.
    compensation_variants = []
    if config.compensation.enabled and valid_candidates:
        weak = select_weak_points(
            base_measurements,
            error_threshold=config.compensation.error_threshold,
            error_metric=config.compensation.error_metric,
            comparison_scope=config.compensation.comparison_scope,
        )
        candidate_map = {candidate.candidate_id: candidate for candidate in valid_candidates}
        backend_map = {backend.name: backend for backend in config.measure.backends}
        compensation_variants = list(
            await asyncio.gather(
                *(
                    generate_compensation(
                        config,
                        oracle,
                        run_dir,
                        execution,
                        candidate_map[point.candidate_id],
                        point,
                        backend_map[point.backend],
                    )
                    for point in weak
                )
            )
        )

    # Phase 5: measure only compensation variants that passed both authoritative FP64
    # validation and the FP32-collapse gate.
    valid_compensation = [
        variant for variant in compensation_variants if variant.status == Status.OK
    ]
    generated_specs = [
        (
            variant.candidate_id,
            variant.variant_id,
            variant.module_path,
            variant.technique,
            variant.backend,
            variant.precision,
        )
        for variant in valid_compensation
    ]
    generated_measurements = await measure_compensation_variants(
        config, oracle, generated_specs, backends
    )
    _reject_non_improving_variants(
        config,
        valid_compensation,
        base_measurements,
        generated_measurements,
    )
    measurements = base_measurements + generated_measurements

    # Phase 6: compute the latency/error frontier and persist the complete experiment,
    # including dominated points and failed attempts retained in their source records.
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
        "security": {
            "execution_mode": f"trusted_{config.execution.mode}_unsandboxed",
            "warning": (
                "Agent-authored Python and enabled execution tools can run arbitrary code on "
                "configured resources; use only trusted configurations and isolated machines."
            ),
        },
        "skills": _skill_records(),
        "execution": {
            "mode": config.execution.mode,
            "default_resource": execution.default_resource,
            "resources": {
                name: report.model_dump(mode="json", exclude={"schema_version"})
                for name, report in (await execution.handshakes()).items()
            },
        },
        "planner": planner_record,
        "candidates": [candidate.to_dict() for candidate in candidates],
        "compensation_variants": [variant.to_dict() for variant in compensation_variants],
        "measurements": [measurement.to_dict() for measurement in measurements],
        "frontier": frontier,
    }
    write_json(run_dir / "run.json", record)
    atomic_write(run_dir / "summary.md", _summary(record))
    return (0 if frontier else 1), run_dir
