"""Resumable, resource-aware multi-candidate pipeline orchestration."""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from types import NoneType
from typing import Any, Protocol, TypeVar

from pydantic_graph import GraphBuilder

from .accelerator import repair_accelerator_candidate, select_compatibility_failures
from .accuracy import candidate_accuracy
from .arena import generate_candidate, plan_strategies
from .artifacts import atomic_write, create_run_dir, write_json, write_resolved_config
from .compensation import (
    CompensationVariant,
    generate_compensation,
    group_portable_weak_points,
    select_weak_points,
)
from .config import RunConfig
from .execution import ExecutionContext
from .measurement import Backend, build_backends, measure_compensation_variants, measure_variants
from .pareto import frontier_indices, valid_point
from .qualification import QualificationResult, qualify_candidate
from .run_record import RunRecord, evaluate_acceptance, render_summary, skill_records
from .scheduler import PipelineScheduler
from .skills import require_automation_skills
from .types import Candidate, Diagnostic, Measurement, PruningDecision, Status
from .validation import OracleResult, build_oracle, load_reference_output
from .visualization import write_pareto_visualizations

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineState:
    """Durable state carried between outer graph steps."""

    oracle: OracleResult | None = None
    strategies: list[str] = field(default_factory=list)
    planner_record: dict[str, Any] = field(default_factory=dict)
    candidates: list[Candidate] = field(default_factory=list)
    valid_candidates: list[Candidate] = field(default_factory=list)
    compatibility_candidates: list[Candidate] = field(default_factory=list)
    numerical_candidates: list[Candidate] = field(default_factory=list)
    compensation_variants: list[CompensationVariant] = field(default_factory=list)
    qualification_results: list[QualificationResult] = field(default_factory=list)
    pruning_decisions: list[PruningDecision] = field(default_factory=list)
    measurements: list[Measurement] = field(default_factory=list)
    frontier: list[dict[str, Any]] = field(default_factory=list)
    visualizations: dict[str, Any] = field(default_factory=dict)
    completed_candidate_ids: list[str] = field(default_factory=list)
    completed_stages: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PipelineDeps:
    config: RunConfig
    config_path: Path
    run_dir: Path
    execution: ExecutionContext
    scheduler: PipelineScheduler
    started_at: str
    started: float
    previous_wall_seconds: float = 0.0


StepInputT_co = TypeVar("StepInputT_co", covariant=True)


class PipelineStepContext(Protocol[StepInputT_co]):
    @property
    def state(self) -> PipelineState: ...

    @property
    def deps(self) -> PipelineDeps: ...

    @property
    def inputs(self) -> StepInputT_co: ...


@dataclass(slots=True)
class CandidateOutcome:
    candidate: Candidate
    base_measurements: list[Measurement] = field(default_factory=list)
    numerical_candidates: list[Candidate] = field(default_factory=list)
    compatibility_candidates: list[Candidate] = field(default_factory=list)
    compensation_variants: list[CompensationVariant] = field(default_factory=list)
    qualifications: list[QualificationResult] = field(default_factory=list)
    pruning: PruningDecision | None = None
    measurements: list[Measurement] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "base_measurements": [item.to_dict() for item in self.base_measurements],
            "numerical_candidates": [item.to_dict() for item in self.numerical_candidates],
            "compatibility_candidates": [item.to_dict() for item in self.compatibility_candidates],
            "compensation_variants": [item.to_dict() for item in self.compensation_variants],
            "qualifications": [item.to_dict() for item in self.qualifications],
            "pruning": self.pruning.to_dict() if self.pruning else None,
            "measurements": [item.to_dict() for item in self.measurements],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CandidateOutcome:
        pruning = value.get("pruning")
        return cls(
            candidate=Candidate.from_dict(value["candidate"]),
            base_measurements=[Measurement.from_dict(item) for item in value["base_measurements"]],
            numerical_candidates=[
                Candidate.from_dict(item) for item in value["numerical_candidates"]
            ],
            compatibility_candidates=[
                Candidate.from_dict(item) for item in value["compatibility_candidates"]
            ],
            compensation_variants=[
                CompensationVariant.from_dict(item) for item in value["compensation_variants"]
            ],
            qualifications=[
                QualificationResult.from_dict(item) for item in value["qualifications"]
            ],
            pruning=PruningDecision(**pruning) if pruning else None,
            measurements=[Measurement.from_dict(item) for item in value["measurements"]],
        )


_skill_records = skill_records
_summary = render_summary
_acceptance = evaluate_acceptance


def _config_hash(config: RunConfig) -> str:
    payload = json.dumps(config.model_dump(mode="json"), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _elapsed(deps: PipelineDeps) -> float:
    return deps.previous_wall_seconds + (time.perf_counter() - deps.started)


def _checkpoint_payload(state: PipelineState, deps: PipelineDeps) -> dict[str, Any]:
    oracle = None
    if state.oracle is not None:
        oracle = {
            "output_path": str(state.oracle.output_path),
            "build_stdout": state.oracle.build_stdout,
            "run_stdout": state.oracle.run_stdout,
            "source_sha256": state.oracle.source_sha256,
            "output_sha256": state.oracle.output_sha256,
            "determinism_runs": state.oracle.determinism_runs,
        }
    return {
        "schema_version": 1,
        "config_sha256": _config_hash(deps.config),
        "started_at": deps.started_at,
        "updated_at": dt.datetime.now(dt.UTC).isoformat(),
        "wall_seconds": round(_elapsed(deps), 3),
        "completed_stages": state.completed_stages,
        "completed_candidate_ids": state.completed_candidate_ids,
        "oracle": oracle,
        "strategies": state.strategies,
        "planner_record": state.planner_record,
        "candidates": [item.to_dict() for item in state.candidates],
        "valid_candidates": [item.to_dict() for item in state.valid_candidates],
        "compatibility_candidates": [item.to_dict() for item in state.compatibility_candidates],
        "numerical_candidates": [item.to_dict() for item in state.numerical_candidates],
        "compensation_variants": [item.to_dict() for item in state.compensation_variants],
        "qualifications": [item.to_dict() for item in state.qualification_results],
        "pruning": [item.to_dict() for item in state.pruning_decisions],
        "measurements": [item.to_dict() for item in state.measurements],
    }


def _save_checkpoint(
    state: PipelineState,
    deps: PipelineDeps,
    stage: str,
    *,
    complete: bool = True,
) -> None:
    if complete and stage not in state.completed_stages:
        state.completed_stages.append(stage)
    write_json(deps.run_dir / "checkpoint.json", _checkpoint_payload(state, deps))


def _load_checkpoint(run_dir: Path, config: RunConfig) -> tuple[PipelineState, str, float]:
    path = run_dir / "checkpoint.json"
    if not path.is_file():
        return PipelineState(), dt.datetime.now(dt.UTC).isoformat(), 0.0
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported pipeline checkpoint schema")
    if payload.get("config_sha256") != _config_hash(config):
        raise ValueError("resume configuration does not match the checkpoint")
    oracle_payload = payload.get("oracle")
    oracle = None
    if oracle_payload:
        output_path = Path(oracle_payload["output_path"])
        oracle = OracleResult(
            output_path=output_path,
            values=load_reference_output(output_path),
            build_stdout=oracle_payload.get("build_stdout", ""),
            run_stdout=oracle_payload.get("run_stdout", ""),
            source_sha256=oracle_payload.get("source_sha256", ""),
            output_sha256=oracle_payload.get("output_sha256", ""),
            determinism_runs=int(oracle_payload.get("determinism_runs", 1)),
        )
    state = PipelineState(
        oracle=oracle,
        strategies=list(payload.get("strategies", [])),
        planner_record=dict(payload.get("planner_record", {})),
        candidates=[Candidate.from_dict(item) for item in payload.get("candidates", [])],
        valid_candidates=[
            Candidate.from_dict(item) for item in payload.get("valid_candidates", [])
        ],
        compatibility_candidates=[
            Candidate.from_dict(item) for item in payload.get("compatibility_candidates", [])
        ],
        numerical_candidates=[
            Candidate.from_dict(item) for item in payload.get("numerical_candidates", [])
        ],
        compensation_variants=[
            CompensationVariant.from_dict(item) for item in payload.get("compensation_variants", [])
        ],
        qualification_results=[
            QualificationResult.from_dict(item) for item in payload.get("qualifications", [])
        ],
        pruning_decisions=[PruningDecision(**item) for item in payload.get("pruning", [])],
        measurements=[Measurement.from_dict(item) for item in payload.get("measurements", [])],
        completed_candidate_ids=list(payload.get("completed_candidate_ids", [])),
        completed_stages=list(payload.get("completed_stages", [])),
    )
    return state, str(payload["started_at"]), float(payload.get("wall_seconds", 0.0))


def _candidate_journal_path(run_dir: Path, candidate_id: str) -> Path:
    return run_dir / "progress" / f"{candidate_id}.json"


def _save_candidate_journal(deps: PipelineDeps, outcome: CandidateOutcome, stage: str) -> None:
    write_json(
        _candidate_journal_path(deps.run_dir, outcome.candidate.candidate_id),
        {
            "schema_version": 1,
            "config_sha256": _config_hash(deps.config),
            "stage": stage,
            "updated_at": dt.datetime.now(dt.UTC).isoformat(),
            "outcome": outcome.to_dict(),
        },
    )


def _load_candidate_journal(
    deps: PipelineDeps, candidate_id: str
) -> tuple[str, CandidateOutcome] | None:
    path = _candidate_journal_path(deps.run_dir, candidate_id)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != 1:
        raise ValueError(f"unsupported candidate checkpoint schema for {candidate_id}")
    if payload.get("config_sha256") != _config_hash(deps.config):
        raise ValueError(f"candidate checkpoint {candidate_id} has a different configuration")
    return str(payload["stage"]), CandidateOutcome.from_dict(payload["outcome"])


def _require_oracle(state: PipelineState) -> OracleResult:
    if state.oracle is None:
        raise RuntimeError("pipeline reached an oracle-dependent step before build_oracle")
    return state.oracle


def _reject_non_improving_variants(
    config: RunConfig,
    variants: list[CompensationVariant],
    base_measurements: list[Measurement],
    generated_measurements: list[Measurement],
) -> None:
    base_by_cell = {
        (point.candidate_id, point.backend, point.precision): point for point in base_measurements
    }
    metric = config.pareto_error_metric
    for variant in variants:
        if variant.status != Status.OK:
            continue
        generated_by_backend = {
            point.backend: point
            for point in generated_measurements
            if point.variant_id == variant.variant_id and point.precision == variant.precision
        }
        failures: list[str] = []
        strict_backends = variant.target_backends or [variant.backend]
        for backend in [*strict_backends, *variant.guard_backends]:
            base = base_by_cell.get((variant.candidate_id, backend, variant.precision))
            generated = generated_by_backend.get(backend)
            if base is None:
                continue
            base_error = getattr(base, metric)
            generated_error = getattr(generated, metric) if generated is not None else None
            strictly_better = backend in strict_backends
            accepted = (
                generated is not None
                and generated.status == Status.OK
                and generated_error is not None
                and generated.evaluation_semantic_verified
                and bool(generated.accuracy_source)
                and (
                    base_error is None
                    or (
                        generated_error < base_error
                        if strictly_better
                        else generated_error <= base_error
                    )
                )
            )
            if not accepted:
                failures.append(
                    f"{backend}/{variant.precision}: base={base_error}, "
                    f"variant={generated_error}, status="
                    f"{generated.status.value if generated else 'missing'}"
                )
        if failures:
            message = f"portable compensation did not improve {metric}: " + "; ".join(failures)
            variant.status = Status.REJECTED
            variant.diagnostics.append(Diagnostic(gate="compensation-effect", message=message))
            for generated in generated_measurements:
                if generated.variant_id == variant.variant_id:
                    generated.status = Status.REJECTED
                    generated.notes = f"{generated.notes}; {message}".strip("; ")


def _all_cells(config: RunConfig) -> set[tuple[str, str]]:
    return {
        (backend.name, precision)
        for backend in config.measure.backends
        for precision in config.measure.precisions
    }


def _measurement_key(point: Measurement) -> tuple[str, str]:
    return point.backend, point.precision


async def _measure_base_candidate(
    deps: PipelineDeps,
    oracle: OracleResult,
    outcome: CandidateOutcome,
    backends: list[Backend[Any]],
) -> bool:
    """Measure one candidate, returning whether it survives optional pruning."""

    config = deps.config
    variant = [
        (
            outcome.candidate.candidate_id,
            f"{outcome.candidate.candidate_id}-base",
            outcome.candidate.module_path,
            "none",
        )
    ]
    existing = {_measurement_key(point) for point in outcome.base_measurements}

    def record(point: Measurement) -> None:
        outcome.base_measurements.append(point)
        outcome.measurements = list(outcome.base_measurements)
        _save_candidate_journal(deps, outcome, "base_measuring")

    if config.pruning.enabled:
        assert config.pruning.probe_backend is not None
        probe = (config.pruning.probe_backend, config.pruning.probe_precision)
        if probe not in existing:
            await measure_variants(
                config,
                oracle,
                variant,
                backends,
                cells={probe},
                on_result=record,
            )
            _save_candidate_journal(deps, outcome, "probe_measured")
        probe_result = next(
            point for point in outcome.base_measurements if _measurement_key(point) == probe
        )
        if not valid_point(probe_result):
            outcome.pruning = PruningDecision(
                outcome.candidate.candidate_id,
                True,
                True,
                probe[0],
                probe[1],
                f"probe status={probe_result.status.value}; "
                f"failure_kind={probe_result.failure_kind}",
            )
            outcome.measurements = list(outcome.base_measurements)
            return False
        outcome.pruning = PruningDecision(
            outcome.candidate.candidate_id,
            True,
            False,
            probe[0],
            probe[1],
            "architectural probe passed",
        )
    else:
        outcome.pruning = PruningDecision(outcome.candidate.candidate_id, False, False)
    remaining = _all_cells(config) - {
        _measurement_key(point) for point in outcome.base_measurements
    }
    if remaining:
        await measure_variants(
            config,
            oracle,
            variant,
            backends,
            cells=remaining,
            on_result=record,
        )
    outcome.measurements = list(outcome.base_measurements)
    return True


async def _candidate_flow(
    deps: PipelineDeps,
    oracle: OracleResult,
    index: int,
    strategy: str,
    backends: list[Backend[Any]],
) -> CandidateOutcome:
    config = deps.config
    scheduler = deps.scheduler
    candidate_id = f"c{index}"
    restored = _load_candidate_journal(deps, candidate_id)
    if restored is None:
        candidate = await scheduler.run_model(
            partial(
                generate_candidate,
                config,
                oracle,
                deps.run_dir,
                deps.execution,
                index,
                strategy,
            )
        )
        stage = "generated"
        outcome = CandidateOutcome(candidate)
        _save_candidate_journal(deps, outcome, stage)
    else:
        stage, outcome = restored
    if stage == "complete" or outcome.candidate.status != Status.OK:
        _save_candidate_journal(deps, outcome, "complete")
        return outcome

    if stage == "generated":

        async def qualify(target: Any, precision: str) -> QualificationResult:
            resource = target.resource or deps.execution.default_resource
            async with scheduler.resource_slot(resource):
                return await qualify_candidate(
                    config, deps.execution, outcome.candidate, target, precision
                )

        qualification_calls = [
            qualify(target, precision)
            for target in config.compatibility.compile_targets
            for precision in target.precisions
        ]
        if qualification_calls:
            outcome.qualifications = list(await asyncio.gather(*qualification_calls))
        failed_required = [
            item for item in outcome.qualifications if item.required and not item.passed
        ]
        if failed_required:
            outcome.candidate.status = Status.REJECTED
            outcome.candidate.diagnostics.extend(
                Diagnostic(
                    gate="compiler-qualification",
                    message=f"{item.target_id}/{item.precision}: {item.status}; {item.notes}",
                )
                for item in failed_required
            )
            _save_candidate_journal(deps, outcome, "complete")
            return outcome
        stage = "qualified"
        _save_candidate_journal(deps, outcome, stage)

    if stage in {"qualified", "probe_measured", "base_measuring"}:
        survived = await _measure_base_candidate(deps, oracle, outcome, backends)
        stage = "base_measured"
        _save_candidate_journal(deps, outcome, stage)
        if not survived:
            _save_candidate_journal(deps, outcome, "complete")
            return outcome

    if stage == "base_measured":
        weak = (
            select_weak_points(
                outcome.base_measurements,
                error_threshold=config.compensation.error_threshold,
                error_metric=config.pareto_error_metric,
                comparison_scope=config.compensation.comparison_scope,
            )
            if config.compensation.enabled
            else []
        )
        backend_specs = {backend.name: backend for backend in config.measure.backends}
        runtime_backends = {backend.spec.name: backend for backend in backends}
        compensation_calls = []
        for group in group_portable_weak_points(weak):
            weak_names = {point.backend for point in group}
            guards = [
                point
                for point in outcome.base_measurements
                if point.candidate_id == outcome.candidate.candidate_id
                and point.precision == group[0].precision
                and point.backend not in weak_names
                and point.status == Status.OK
                and getattr(point, config.pareto_error_metric) is not None
            ]
            names = sorted({point.backend for point in [*group, *guards]})
            compensation_calls.append(
                scheduler.run_model(
                    partial(
                        generate_compensation,
                        config,
                        oracle,
                        deps.run_dir,
                        deps.execution,
                        outcome.candidate,
                        group,
                        [backend_specs[name] for name in names],
                        target_backends=runtime_backends,
                        guard_points=guards,
                    )
                )
            )
        if compensation_calls:
            outcome.compensation_variants = list(await asyncio.gather(*compensation_calls))
        stage = "compensation_generated"
        _save_candidate_journal(deps, outcome, stage)

    if stage in {"compensation_generated", "compensation_measuring"}:
        valid_variants = [
            variant for variant in outcome.compensation_variants if variant.status == Status.OK
        ]
        specs = [
            (
                variant.candidate_id,
                variant.variant_id,
                variant.module_path,
                variant.technique,
                variant.backend,
                variant.precision,
            )
            for variant in valid_variants
        ]
        generated: list[Measurement] = []

        def record_generated(point: Measurement) -> None:
            generated.append(point)
            outcome.measurements = outcome.base_measurements + generated
            _save_candidate_journal(deps, outcome, "compensation_measuring")

        await measure_compensation_variants(
            config,
            oracle,
            specs,
            backends,
            on_result=record_generated,
        )
        _reject_non_improving_variants(config, valid_variants, outcome.base_measurements, generated)
        outcome.numerical_candidates = [
            Candidate(
                candidate_id=variant.variant_id,
                model=outcome.candidate.model,
                provider=outcome.candidate.provider,
                strategy=(
                    f"Portable {variant.precision} numerical variant of "
                    f"{variant.candidate_id}: {variant.technique}"
                ),
                module_path=variant.module_path,
                reasoning_effort=outcome.candidate.reasoning_effort,
                status=Status.OK,
                parent_candidate_id=variant.candidate_id,
                target_precision=variant.precision,
            )
            for variant in valid_variants
            if variant.status == Status.OK
        ]
        outcome.measurements = outcome.base_measurements + generated
        stage = "compensated"
        _save_candidate_journal(deps, outcome, stage)

    if stage == "compensated":
        failures = select_compatibility_failures(config, outcome.measurements)
        candidate_map = {
            candidate.candidate_id: candidate
            for candidate in [outcome.candidate, *outcome.numerical_candidates]
        }
        backend_map = {backend.spec.name: backend for backend in backends}
        repairs = [
            scheduler.run_model(
                partial(
                    repair_accelerator_candidate,
                    config,
                    oracle,
                    deps.run_dir,
                    deps.execution,
                    candidate_map[
                        point.variant_id if point.compensation != "none" else point.candidate_id
                    ],
                    point,
                    backend_map[point.backend],
                )
            )
            for point in failures
        ]
        repaired = list(await asyncio.gather(*repairs)) if repairs else []
        outcome.compatibility_candidates = [candidate for candidate, _ in repaired]
        outcome.measurements.extend(
            measurement for _, measurement in repaired if measurement is not None
        )
        _save_candidate_journal(deps, outcome, "repaired")

    _save_candidate_journal(deps, outcome, "complete")
    return outcome


def _merge_outcome(state: PipelineState, outcome: CandidateOutcome) -> None:
    candidate_id = outcome.candidate.candidate_id
    if candidate_id in state.completed_candidate_ids:
        return
    state.candidates.append(outcome.candidate)
    if outcome.candidate.status == Status.OK:
        state.valid_candidates.append(outcome.candidate)
    state.numerical_candidates.extend(outcome.numerical_candidates)
    state.compatibility_candidates.extend(outcome.compatibility_candidates)
    state.valid_candidates.extend(outcome.numerical_candidates)
    state.valid_candidates.extend(
        item for item in outcome.compatibility_candidates if item.status == Status.OK
    )
    state.compensation_variants.extend(outcome.compensation_variants)
    state.qualification_results.extend(outcome.qualifications)
    if outcome.pruning is not None:
        state.pruning_decisions.append(outcome.pruning)
    state.measurements.extend(outcome.measurements)
    state.completed_candidate_ids.append(candidate_id)


_pipeline_graph_builder = GraphBuilder(
    name="lassi_x_pipeline",
    state_type=PipelineState,
    deps_type=PipelineDeps,
    input_type=NoneType,
    output_type=tuple[int, Path],
    auto_instrument=False,
)


@_pipeline_graph_builder.step(node_id="build_oracle", label="Build FP64 C/C++ oracle")
async def _build_oracle_step(ctx: PipelineStepContext[None]) -> None:
    if "build_oracle" not in ctx.state.completed_stages:
        ctx.state.oracle = await build_oracle(ctx.deps.config, ctx.deps.run_dir)
        _save_checkpoint(ctx.state, ctx.deps, "build_oracle")


@_pipeline_graph_builder.step(node_id="plan_strategies", label="Plan candidate strategies")
async def _plan_strategies_step(ctx: PipelineStepContext[None]) -> None:
    if "plan_strategies" not in ctx.state.completed_stages:
        ctx.state.strategies, ctx.state.planner_record = await ctx.deps.scheduler.run_model(
            partial(plan_strategies, ctx.deps.config, ctx.deps.run_dir)
        )
        _save_checkpoint(ctx.state, ctx.deps, "plan_strategies")


@_pipeline_graph_builder.step(
    node_id="stream_candidates",
    label="Stream candidate qualification, pruning, measurement and repair",
)
async def _stream_candidates_step(ctx: PipelineStepContext[None]) -> None:
    if "stream_candidates" in ctx.state.completed_stages:
        return
    backends = build_backends(ctx.deps.config, ctx.deps.execution, ctx.deps.scheduler)
    completed = set(ctx.state.completed_candidate_ids)
    tasks = [
        asyncio.create_task(
            ctx.deps.scheduler.run_candidate(
                partial(
                    _candidate_flow,
                    ctx.deps,
                    _require_oracle(ctx.state),
                    index,
                    strategy,
                    backends,
                )
            )
        )
        for index, strategy in enumerate(ctx.state.strategies, 1)
        if f"c{index}" not in completed
    ]
    try:
        for task in asyncio.as_completed(tasks):
            outcome = await task
            _merge_outcome(ctx.state, outcome)
            _save_checkpoint(ctx.state, ctx.deps, "stream_candidates", complete=False)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    ctx.state.candidates.sort(key=lambda item: item.candidate_id)
    _save_checkpoint(ctx.state, ctx.deps, "stream_candidates")


@_pipeline_graph_builder.step(
    node_id="finalize", label="Build architectural frontier and artifacts"
)
async def _finalize_step(ctx: PipelineStepContext[None]) -> tuple[int, Path]:
    state = ctx.state
    deps = ctx.deps
    config = deps.config
    oracle = _require_oracle(state)
    if config.evaluation_dataset == config.kernel.validation_dataset:
        evaluation_oracle_path = oracle.output_path
    else:
        assert config.evaluation_oracle is not None
        evaluation_oracle_path = config.resolve_project_path(config.evaluation_oracle)
    indices = frontier_indices(state.measurements)
    state.frontier = [state.measurements[index].to_dict() for index in indices]
    acceptance = _acceptance(config, state.measurements)
    status = "failed" if not state.frontier else ("ok" if acceptance["passed"] else "partial")
    atomic_write(
        deps.run_dir / "measurements.jsonl",
        "".join(json.dumps(item.to_dict(), default=str) + "\n" for item in state.measurements),
    )
    write_json(deps.run_dir / "frontier.json", state.frontier)
    state.visualizations = write_pareto_visualizations(
        deps.run_dir / "visualizations", state.measurements
    )
    _save_checkpoint(state, deps, "finalize")
    record = RunRecord.model_validate(
        {
            "schema_version": 1,
            "status": status,
            "kernel": config.kernel.name,
            "started_at": deps.started_at,
            "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            "wall_seconds": round(_elapsed(deps), 3),
            "config_path": str(deps.config_path.resolve()),
            "oracle": {
                "kind": "c_reference_fp64",
                "dataset": config.kernel.validation_dataset,
                "reference_path": str(config.resolve_project_path(config.kernel.reference)),
                "output_path": str(oracle.output_path),
                "numel": int(oracle.values.size),
                "source_sha256": oracle.source_sha256,
                "output_sha256": oracle.output_sha256,
                "determinism_runs": oracle.determinism_runs,
            },
            "datasets": {
                "cpu_validation": config.kernel.validation_dataset,
                "evaluation": config.evaluation_dataset,
            },
            "security": {
                "execution_mode": f"trusted_{config.execution.mode}_unsandboxed",
                "warning": "Agent-authored code runs on trusted configured resources.",
            },
            "evaluation": {
                "oracle_determinism_runs": oracle.determinism_runs,
                "oracle_source_sha256": oracle.source_sha256,
                "oracle_output_sha256": oracle.output_sha256,
                "device_accuracy_latency_pair_required": True,
                "evaluation_oracle": str(evaluation_oracle_path),
                "evaluation_oracle_sha256": hashlib.sha256(
                    evaluation_oracle_path.read_bytes()
                ).hexdigest(),
                "evaluation_semantic_verification_required": True,
                "candidate_input_owner": "candidate_module",
                "sealed_holdout": False,
                "isolation": "trusted_workspace_cwd_not_os_sandbox",
                "pareto_timing_protocol": "architectural-single-call-v1",
                "host_timing_accepted": False,
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
            "scheduler": config.scheduler.model_dump(mode="json"),
            "qualifications": [item.to_dict() for item in state.qualification_results],
            "pruning": [item.to_dict() for item in state.pruning_decisions],
            "checkpoint": {
                "schema_version": 1,
                "path": str(deps.run_dir / "checkpoint.json"),
                "resumable": True,
                "completed_stages": state.completed_stages,
            },
            "acceptance": acceptance,
            "pareto_error_metric": config.pareto_error_metric,
            "accuracy": candidate_accuracy(state.candidates),
            "candidates": [item.to_dict() for item in state.candidates],
            "compatibility_candidates": [item.to_dict() for item in state.compatibility_candidates],
            "numerical_candidates": [item.to_dict() for item in state.numerical_candidates],
            "compensation_variants": [item.to_dict() for item in state.compensation_variants],
            "measurements": [item.to_dict() for item in state.measurements],
            "frontier": state.frontier,
            "visualizations": state.visualizations,
        }
    )
    write_json(deps.run_dir / "run.json", record.model_dump(mode="json"))
    atomic_write(deps.run_dir / "summary.md", _summary(record))
    return (0 if status == "ok" else 1), deps.run_dir


_pipeline_graph_builder.add(
    _pipeline_graph_builder.edge_from(_pipeline_graph_builder.start_node).to(_build_oracle_step),
    _pipeline_graph_builder.edge_from(_build_oracle_step).to(_plan_strategies_step),
    _pipeline_graph_builder.edge_from(_plan_strategies_step).to(_stream_candidates_step),
    _pipeline_graph_builder.edge_from(_stream_candidates_step).to(_finalize_step),
    _pipeline_graph_builder.edge_from(_finalize_step).to(_pipeline_graph_builder.end_node),
)
PIPELINE_GRAPH = _pipeline_graph_builder.build()


async def run_pipeline(config_path: Path, *, resume_dir: Path | None = None) -> tuple[int, Path]:
    """Execute or resume the complete translation and measurement pipeline."""

    require_automation_skills()
    config = RunConfig.load(config_path)
    run_root = (
        config.runs_dir if config.runs_dir.is_absolute() else config.project.root / config.runs_dir
    )
    if resume_dir is None:
        run_dir = create_run_dir(run_root, config.kernel.name)
        write_resolved_config(run_dir / "resolved-config.yaml", config.model_dump(mode="json"))
        state = PipelineState()
        started_at = dt.datetime.now(dt.UTC).isoformat()
        previous_wall_seconds = 0.0
    else:
        run_dir = resume_dir.resolve()
        if not run_dir.is_dir():
            raise ValueError(f"resume directory does not exist: {run_dir}")
        state, started_at, previous_wall_seconds = _load_checkpoint(run_dir, config)
    started = time.perf_counter()
    try:
        async with await ExecutionContext.start(config, run_dir) as execution:
            deps = PipelineDeps(
                config,
                config_path,
                run_dir,
                execution,
                PipelineScheduler(config.scheduler),
                started_at,
                started,
                previous_wall_seconds,
            )
            atomic_write(
                run_dir / "pipeline-graph.mmd",
                PIPELINE_GRAPH.render(title="LASSI-X pipeline", direction="LR") + "\n",
            )
            return await PIPELINE_GRAPH.run(state=state, deps=deps, inputs=None)
    except Exception as exc:
        logger.exception("pipeline failed: kernel=%s error=%s", config.kernel.name, exc)
        record = {
            "schema_version": 1,
            "status": "failed",
            "kernel": config.kernel.name,
            "started_at": started_at,
            "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            "wall_seconds": round(previous_wall_seconds + time.perf_counter() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "checkpoint": str(run_dir / "checkpoint.json"),
            "completed_stages": state.completed_stages,
            "completed_candidate_ids": state.completed_candidate_ids,
        }
        write_json(run_dir / "run.json", record)
        atomic_write(
            run_dir / "summary.md",
            f"# LASSI-X run: {config.kernel.name}\n\n"
            f"- Status: **failed**\n- Error: `{record['error']}`\n"
            f"- Resume: `lassi-x run {config_path} --resume {run_dir}`\n",
        )
        return 1, run_dir
