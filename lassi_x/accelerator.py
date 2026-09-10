"""Whole-candidate accelerator qualification and compatibility repair."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any

from .agent_support import (
    attempt_diagnostic_dir,
    record_turn,
    stage_reference_bundle,
    workspace_slug,
)
from .hermes import HermesSession
from .types import Candidate, Diagnostic, Measurement, Status
from .validation import validate_candidate

if TYPE_CHECKING:
    from pathlib import Path

    from .config import RunConfig
    from .execution import ExecutionContext
    from .measurement import Backend
    from .validation import OracleResult


COMPATIBILITY_SYSTEM = """Role: accelerator compiler compatibility engineer.

You receive an FP64-correct PyTorch candidate that failed on one real accelerator/compiler cell.
Repair only operator structure, graph lowering, static-shape behavior, or placement pressure. Load
and follow lassi-x-accelerator-compatibility, select the exact published target snapshot, inventory
the candidate's actual or expected aten operators, and query every uncertain operator with
lassi-x-compat-wiki. Compiler diagnostics and real whole-graph execution override wiki preflight.

Preserve the authoritative C/C++ semantics. Never weaken validation, embed oracle values, replace
an operation with a merely similar one, or introduce low-precision numerical compensation in this
stage. Every edit must still pass the external CPU FP64 oracle before it is tried on the target.

Use only the assigned workspace tools and edit only candidate.py. Report evidence actually
observed, including target ID, queried operators, substitutions, and checks run.
"""


def _accelerator_backend_names(config: RunConfig) -> set[str]:
    """Return configured backends that are not ordinary CPU eager execution."""

    return {
        spec.name
        for spec in config.measure.backends
        if spec.type in {"groq", "native"}
        or (spec.type == "torch" and str(spec.device).partition(":")[0] != "cpu")
    }


def select_compatibility_failures(
    config: RunConfig, measurements: list[Measurement]
) -> list[Measurement]:
    """Select each source-repairable source-variant/backend/precision failure."""

    if not config.compatibility.enabled:
        return []
    accelerator_names = _accelerator_backend_names(config)
    repair_statuses = {Status(value) for value in config.compatibility.repair_statuses}
    nonrepairable_kinds = {
        "infrastructure_submission",
        "infrastructure_timeout",
        "resource_unavailable",
        "submission_timeout",
        "execution_timeout",
        "precision_unsupported",
    }
    precision_order = {"fp32": 0, "fp16": 1, "bf16": 2, "fp64": 3}
    eligible = sorted(
        (
            point
            for point in measurements
            if "compatibility" not in point.compensation
            and point.backend in accelerator_names
            and (
                point.status in repair_statuses
                or (
                    point.status == Status.DIVERGED
                    and point.precision in config.measure.strict_precisions
                )
            )
            and point.failure_kind not in nonrepairable_kinds
        ),
        key=lambda point: (
            point.variant_id,
            point.backend,
            precision_order.get(point.precision, 99),
        ),
    )
    selected: dict[tuple[str, str, str], Measurement] = {}
    for point in eligible:
        selected.setdefault((point.variant_id, point.backend, point.precision), point)
    return list(selected.values())


def _candidate_model(config: RunConfig, candidate: Candidate) -> Any:
    if config.models.compatibility is not None:
        return config.models.compatibility
    for model in config.models.candidates:
        if model.model == candidate.model and model.provider == candidate.provider:
            return model
    match = re.fullmatch(r"c(\d+)", candidate.candidate_id)
    index = int(match.group(1)) - 1 if match else 0
    return config.models.candidates[min(max(index, 0), len(config.models.candidates) - 1)]


def compatibility_accuracy_diagnostic(
    config: RunConfig,
    parent: Measurement,
    patched: Measurement,
) -> Diagnostic | None:
    """Require a compatibility leaf to preserve a device-derived accuracy contract."""

    metric = config.pareto_error_metric
    patched_error = getattr(patched, metric, None)
    if (
        patched.status != Status.OK
        or patched_error is None
        or not math.isfinite(patched_error)
        or not patched.evaluation_semantic_verified
        or not patched.accuracy_source
    ):
        return Diagnostic(
            gate="compatibility-accuracy",
            message=(
                f"patched {patched.backend}/{patched.precision} did not produce a successful "
                f"finite device {metric} paired with latency: status={patched.status.value}, "
                f"error={patched_error}; {patched.notes}"
            ),
        )
    parent_error = getattr(parent, metric, None)
    if parent_error is not None and math.isfinite(parent_error) and patched_error > parent_error:
        return Diagnostic(
            gate="compatibility-accuracy",
            message=(
                f"compatibility patch regressed device {metric}: "
                f"parent={parent_error:.8e}, patched={patched_error:.8e}"
            ),
        )
    threshold = config.compensation.error_threshold
    if (
        parent_error is None
        and patched.precision in {"fp16", "bf16"}
        and threshold is not None
        and patched_error > threshold
    ):
        return Diagnostic(
            gate="compatibility-accuracy",
            message=(
                f"compatibility patch became executable but device {metric}={patched_error:.8e} "
                f"exceeds the acceptance threshold {threshold:.8e}"
            ),
        )
    return None


async def repair_accelerator_candidate(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
    execution: ExecutionContext,
    base: Candidate,
    failure: Measurement,
    backend: Backend[Any],
) -> tuple[Candidate, Measurement | None]:
    """Repair one target failure with CPU semantic and real-target feedback gates."""

    raw_slug = f"a-{base.candidate_id}-{failure.backend}-{failure.precision}"
    slug = workspace_slug(raw_slug)
    mirror = execution.workspace_dir(slug)
    mirror.mkdir(parents=True, exist_ok=True)
    toolset = execution.register_workspace(slug)
    await execution.stage_bytes(slug, "candidate.py", base.module_path.read_bytes())
    staged = await stage_reference_bundle(config, execution, slug)
    model = _candidate_model(config, base)
    candidate = Candidate(
        candidate_id=slug,
        model=model.model,
        provider=model.provider,
        strategy=f"Accelerator repair of {base.candidate_id} for {failure.backend}",
        module_path=mirror / "candidate.py",
        reasoning_effort=model.reasoning_effort,
        parent_candidate_id=base.candidate_id,
        target_backend=failure.backend,
        target_precision=failure.precision,
    )
    references = "\n".join(f"- {path}" for path in staged)
    prompt = f"""Repair this whole-candidate accelerator failure.

Target file: candidate.py
Authoritative sources:
{references}
Backend: {failure.backend}
Precision: {failure.precision}
Observed status: {failure.status.value}
Parent device {config.pareto_error_metric}: {getattr(failure, config.pareto_error_metric, None)}
Observed compiler/runtime evidence: {failure.notes or "no diagnostic text was returned"}

Start by reading candidate.py and the reference. Use the exact compatibility wiki workflow, make
one semantically faithful source change, and byte-compile candidate.py. Return a concise evidence
summary. The harness will run CPU FP64 validation and then the real target, and will reject any
loss of the parent's device accuracy; do not claim success before those gates report it.
"""
    session = HermesSession(
        model,
        cwd=mirror,
        system_prompt=COMPATIBILITY_SYSTEM,
        toolsets=["skills", toolset],
        role=f"compatibility-{slug}",
        memory=config.memory,
    )
    target_measurement: Measurement | None = None
    try:
        turn = await session.send(prompt)
        record_turn(candidate, turn)
        for attempt in range(config.compatibility.correction_rounds + 1):
            await execution.mirror_file(slug, "candidate.py")
            diagnostic_dir = attempt_diagnostic_dir(run_dir, "accelerator", slug, attempt)
            validation = await validate_candidate(
                config, execution.backend(), slug, oracle, diagnostic_dir
            )
            diagnostic = validation.diagnostic
            if validation.ok:
                target_measurement = await backend.measure(
                    config,
                    oracle,
                    candidate.module_path,
                    candidate_id=candidate.candidate_id,
                    variant_id=f"{candidate.candidate_id}-base",
                    precision=failure.precision,
                    compensation=(
                        "compatibility-repair"
                        if failure.compensation == "none"
                        else f"{failure.compensation}+compatibility"
                    ),
                )
                accuracy_diagnostic = compatibility_accuracy_diagnostic(
                    config, failure, target_measurement
                )
                if accuracy_diagnostic is None:
                    candidate.status = Status.OK
                    await execution.mirror_file(slug, "candidate.py")
                    break
                diagnostic = accuracy_diagnostic
                if target_measurement.status in {Status.UNSUPPORTED, Status.TIMEOUT}:
                    candidate.status = target_measurement.status
                    candidate.diagnostics.append(diagnostic)
                    break
            if diagnostic is None:
                diagnostic = Diagnostic(
                    gate="accelerator-compatibility",
                    message="accelerator qualification failed without diagnostic evidence",
                )
            candidate.diagnostics.append(diagnostic)
            if attempt >= config.compatibility.correction_rounds:
                candidate.status = Status.REJECTED
                break
            candidate.correction_rounds += 1
            turn = await session.send(
                f"""Compatibility correction round {candidate.correction_rounds}.

The external gate rejected candidate.py:

{diagnostic.for_agent()}

Re-query the exact target wiki for implicated operators, repair the root compiler/graph issue,
preserve CPU FP64 semantics, and byte-compile the file. Return a concise evidence summary.
"""
            )
            record_turn(candidate, turn)
    except Exception as exc:
        candidate.status = Status.CRASHED
        candidate.diagnostics.append(
            Diagnostic(gate="compatibility-agent", message=f"{type(exc).__name__}: {exc}")
        )
    finally:
        await session.close()
    return candidate, target_measurement
