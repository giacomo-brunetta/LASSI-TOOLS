from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import NoneType
from typing import Any, Protocol, TypeVar

from pydantic_graph import GraphBuilder

from .accuracy import candidate_accuracy
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
    Backend,
    build_backends,
    measure_compensation_variants,
    measure_variants,
)
from .pareto import frontier_indices
from .skills import AUTOMATION_SKILLS, install_root, require_automation_skills
from .types import Candidate, Diagnostic, Measurement, Status
from .validation import OracleResult, build_oracle
from .visualization import write_pareto_visualizations


@dataclass(slots=True)
class PipelineState:
    """Mutable state carried between typed Pydantic Graph steps."""

    oracle: OracleResult | None = None
    candidates: list[Candidate] = field(default_factory=list)
    planner_record: dict[str, Any] = field(default_factory=dict)
    valid_candidates: list[Candidate] = field(default_factory=list)
    backends: list[Backend] = field(default_factory=list)
    base_measurements: list[Measurement] = field(default_factory=list)
    weak_points: list[Measurement] = field(default_factory=list)
    compensation_variants: list[CompensationVariant] = field(default_factory=list)
    generated_measurements: list[Measurement] = field(default_factory=list)
    measurements: list[Measurement] = field(default_factory=list)
    frontier: list[dict[str, Any]] = field(default_factory=list)
    visualizations: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PipelineDeps:
    """Immutable services and run metadata injected into every graph step."""

    config: RunConfig
    config_path: Path
    run_dir: Path
    execution: ExecutionContext
    started_at: str
    started: float


StepInputT_co = TypeVar("StepInputT_co", covariant=True)


class PipelineStepContext(Protocol[StepInputT_co]):
    """Mypy-compatible view of the Pydantic Graph step context."""

    @property
    def state(self) -> PipelineState:
        """Return the mutable pipeline state."""
        ...

    @property
    def deps(self) -> PipelineDeps:
        """Return immutable pipeline dependencies."""
        ...

    @property
    def inputs(self) -> StepInputT_co:
        """Return the value routed into the current graph step."""
        ...


@dataclass(frozen=True, slots=True)
class CompensationRequired:
    """Route marker indicating that weak low-precision cells need repair."""


@dataclass(frozen=True, slots=True)
class CompensationSkipped:
    """Route marker indicating that no compensation work is required."""


@dataclass(frozen=True, slots=True)
class CompensationReady:
    """Convergence marker emitted by both compensation graph branches."""


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
        f"- Accuracy dataset: `{record['datasets']['accuracy']}`",
        f"- Performance dataset: `{record['datasets']['performance']}`",
        f"- Candidates generated: {len(candidates)}",
        f"- Candidates passing FP64 reference validation: "
        f"{sum(c['status'] == 'ok' for c in candidates)}",
        f"- Compensation variants: {len(record['compensation_variants'])}",
        f"- Measurements: {len(measurements)}",
        f"- Frontier points: {len(frontier)}",
        f"- Pareto plots: [overall]({record['visualizations']['overall']['svg']})",
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


def _require_oracle(state: PipelineState) -> OracleResult:
    """Return the oracle after its graph step has completed.

    Args:
        state: Current pipeline graph state.

    Returns:
        The authoritative oracle result.

    Raises:
        RuntimeError: If graph execution reaches an oracle-dependent step out of order.

    """
    if state.oracle is None:
        raise RuntimeError("pipeline graph reached an oracle-dependent step before build_oracle")
    return state.oracle


_pipeline_graph_builder = GraphBuilder(
    name="lassi_x_pipeline",
    state_type=PipelineState,
    deps_type=PipelineDeps,
    input_type=NoneType,
    output_type=tuple[int, Path],
    auto_instrument=False,
)


@_pipeline_graph_builder.step(node_id="build_oracle", label="Build FP64 C/C++ oracle")
async def _build_oracle_step(
    ctx: PipelineStepContext[None],
) -> None:
    """Build and store the independent FP64 reference oracle.

    Args:
        ctx: Graph context containing mutable state and immutable run dependencies.

    """
    ctx.state.oracle = await build_oracle(ctx.deps.config, ctx.deps.run_dir)


@_pipeline_graph_builder.step(node_id="run_arena", label="Plan and validate candidates")
async def _run_arena_step(
    ctx: PipelineStepContext[None],
) -> None:
    """Generate arena candidates and retain those passing FP64 validation.

    Args:
        ctx: Graph context whose state already contains the oracle.

    """
    candidates, planner_record = await run_arena(
        ctx.deps.config,
        _require_oracle(ctx.state),
        ctx.deps.run_dir,
        ctx.deps.execution,
    )
    ctx.state.candidates = candidates
    ctx.state.planner_record = planner_record
    ctx.state.valid_candidates = [
        candidate for candidate in candidates if candidate.status == Status.OK
    ]


@_pipeline_graph_builder.step(node_id="measure_base", label="Measure accepted candidates")
async def _measure_base_step(
    ctx: PipelineStepContext[None],
) -> None:
    """Measure every accepted base candidate across configured cells.

    Args:
        ctx: Graph context containing validated candidates and the oracle.

    """
    ctx.state.backends = build_backends(ctx.deps.config, ctx.deps.execution)
    base_variants = [
        (
            candidate.candidate_id,
            f"{candidate.candidate_id}-base",
            candidate.module_path,
            "none",
        )
        for candidate in ctx.state.valid_candidates
    ]
    ctx.state.base_measurements = await measure_variants(
        ctx.deps.config,
        _require_oracle(ctx.state),
        base_variants,
        ctx.state.backends,
    )


@_pipeline_graph_builder.step(
    node_id="route_compensation",
    label="Select weak low-precision cells",
)
async def _route_compensation_step(
    ctx: PipelineStepContext[None],
) -> CompensationRequired | CompensationSkipped:
    """Select weak points and choose the compensation or bypass branch.

    Args:
        ctx: Graph context containing base measurements and compensation policy.

    Returns:
        A typed route marker consumed by the graph decision node.

    """
    config = ctx.deps.config
    if not config.compensation.enabled or not ctx.state.valid_candidates:
        ctx.state.weak_points = []
        return CompensationSkipped()
    ctx.state.weak_points = select_weak_points(
        ctx.state.base_measurements,
        error_threshold=config.compensation.error_threshold,
        error_metric=config.compensation.error_metric,
        comparison_scope=config.compensation.comparison_scope,
    )
    return CompensationRequired() if ctx.state.weak_points else CompensationSkipped()


@_pipeline_graph_builder.step(
    node_id="generate_compensation",
    label="Generate and validate corrections",
)
async def _generate_compensation_step(
    ctx: PipelineStepContext[CompensationRequired],
) -> CompensationReady:
    """Generate compensation variants concurrently for selected weak cells.

    Args:
        ctx: Graph context routed through the compensation-required branch.

    Returns:
        A convergence marker for downstream compensated measurement.

    """
    config = ctx.deps.config
    candidate_map = {candidate.candidate_id: candidate for candidate in ctx.state.valid_candidates}
    backend_map = {backend.name: backend for backend in config.measure.backends}
    ctx.state.compensation_variants = list(
        await asyncio.gather(
            *(
                generate_compensation(
                    config,
                    _require_oracle(ctx.state),
                    ctx.deps.run_dir,
                    ctx.deps.execution,
                    candidate_map[point.candidate_id],
                    point,
                    backend_map[point.backend],
                )
                for point in ctx.state.weak_points
            )
        )
    )
    return CompensationReady()


@_pipeline_graph_builder.step(node_id="skip_compensation", label="Bypass correction")
async def _skip_compensation_step(
    ctx: PipelineStepContext[CompensationSkipped],
) -> CompensationReady:
    """Converge the no-compensation branch without generating variants.

    Args:
        ctx: Graph context routed through the compensation-skipped branch.

    Returns:
        A convergence marker for downstream compensated measurement.

    """
    ctx.state.compensation_variants = []
    return CompensationReady()


@_pipeline_graph_builder.step(
    node_id="measure_compensation",
    label="Measure validated corrections",
)
async def _measure_compensation_step(
    ctx: PipelineStepContext[CompensationReady],
) -> None:
    """Measure valid compensation variants and reject non-improvements.

    Args:
        ctx: Graph context after either compensation branch has converged.

    """
    valid_compensation = [
        variant for variant in ctx.state.compensation_variants if variant.status == Status.OK
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
    ctx.state.generated_measurements = await measure_compensation_variants(
        ctx.deps.config,
        _require_oracle(ctx.state),
        generated_specs,
        ctx.state.backends,
    )
    _reject_non_improving_variants(
        ctx.deps.config,
        valid_compensation,
        ctx.state.base_measurements,
        ctx.state.generated_measurements,
    )
    ctx.state.measurements = ctx.state.base_measurements + ctx.state.generated_measurements


@_pipeline_graph_builder.step(node_id="finalize", label="Build frontier and artifacts")
async def _finalize_step(
    ctx: PipelineStepContext[None],
) -> tuple[int, Path]:
    """Compute the Pareto frontier and persist the complete run record.

    Args:
        ctx: Graph context containing all candidate and measurement outcomes.

    Returns:
        A process-style exit code and the immutable run directory.

    """
    state = ctx.state
    deps = ctx.deps
    config = deps.config
    oracle = _require_oracle(state)
    indices = frontier_indices(state.measurements)
    state.frontier = [state.measurements[index].to_dict() for index in indices]
    status = "ok" if state.frontier else "failed"
    for measurement in state.measurements:
        append_jsonl(deps.run_dir / "measurements.jsonl", measurement.to_dict())
    write_json(deps.run_dir / "frontier.json", state.frontier)
    state.visualizations = write_pareto_visualizations(
        deps.run_dir / "visualizations",
        state.measurements,
    )
    record = {
        "schema_version": 1,
        "status": status,
        "kernel": config.kernel.name,
        "started_at": deps.started_at,
        "finished_at": dt.datetime.now(dt.UTC).isoformat(),
        "wall_seconds": round(time.perf_counter() - deps.started, 3),
        "config_path": str(deps.config_path.resolve()),
        "oracle": {
            "kind": "c_reference_fp64",
            "dataset": config.kernel.validation_dataset,
            "reference_path": str(config.resolve_project_path(config.kernel.reference)),
            "output_path": str(oracle.output_path),
            "numel": int(oracle.values.size),
        },
        "datasets": {
            "accuracy": config.kernel.validation_dataset,
            "performance": config.measure.performance_dataset,
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
            "default_resource": deps.execution.default_resource,
            "resources": {
                name: report.model_dump(mode="json", exclude={"schema_version"})
                for name, report in (await deps.execution.handshakes()).items()
            },
        },
        "planner": state.planner_record,
        "accuracy": candidate_accuracy(state.candidates),
        "candidates": [candidate.to_dict() for candidate in state.candidates],
        "compensation_variants": [variant.to_dict() for variant in state.compensation_variants],
        "measurements": [measurement.to_dict() for measurement in state.measurements],
        "frontier": state.frontier,
        "visualizations": state.visualizations,
    }
    write_json(deps.run_dir / "run.json", record)
    atomic_write(deps.run_dir / "summary.md", _summary(record))
    return (0 if state.frontier else 1), deps.run_dir


_compensation_decision = (
    _pipeline_graph_builder.decision(
        node_id="compensation_decision",
        note="Generate corrections only when weak FP16/BF16 cells were selected.",
    )
    .branch(_pipeline_graph_builder.match(CompensationRequired).to(_generate_compensation_step))
    .branch(_pipeline_graph_builder.match(CompensationSkipped).to(_skip_compensation_step))
)
_pipeline_graph_builder.add(
    _pipeline_graph_builder.edge_from(_pipeline_graph_builder.start_node).to(_build_oracle_step),
    _pipeline_graph_builder.edge_from(_build_oracle_step).to(_run_arena_step),
    _pipeline_graph_builder.edge_from(_run_arena_step).to(_measure_base_step),
    _pipeline_graph_builder.edge_from(_measure_base_step).to(_route_compensation_step),
    _pipeline_graph_builder.edge_from(_route_compensation_step).to(_compensation_decision),
    _pipeline_graph_builder.edge_from(
        _generate_compensation_step,
        _skip_compensation_step,
    ).to(_measure_compensation_step),
    _pipeline_graph_builder.edge_from(_measure_compensation_step).to(_finalize_step),
    _pipeline_graph_builder.edge_from(_finalize_step).to(_pipeline_graph_builder.end_node),
)
PIPELINE_GRAPH = _pipeline_graph_builder.build()


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
    deps = PipelineDeps(
        config=config,
        config_path=config_path,
        run_dir=run_dir,
        execution=execution,
        started_at=started_at,
        started=started,
    )
    atomic_write(
        run_dir / "pipeline-graph.mmd",
        PIPELINE_GRAPH.render(title="LASSI-X pipeline", direction="LR") + "\n",
    )
    return await PIPELINE_GRAPH.run(
        state=PipelineState(),
        deps=deps,
        inputs=None,
    )
