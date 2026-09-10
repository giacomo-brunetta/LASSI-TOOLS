from __future__ import annotations

import ast
import asyncio
import json
import re
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from .agent_support import attempt_diagnostic_dir, record_turn, workspace_slug
from .hermes import HermesSession
from .types import Candidate, Diagnostic, Measurement, Status, Usage
from .validation import (
    OracleResult,
    fixture_relative_path,
    validate_candidate,
    validate_fp32_collapse,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from .config import BackendConfig, RunConfig
    from .execution import ExecutionContext
    from .measurement import Backend

COMPENSATION_SYSTEM = """Role: senior numerical analyst specializing in low-precision
scientific computing and compensated arithmetic.

You own one already-correct PyTorch translation and must make a portable FP16/BF16
intervention for all named backends. Diagnose the shared numerical failure, choose a technique
whose assumptions hold across the declared capability intersection, and implement one substantive
source change that improves low-precision behavior without changing the underlying algorithm.

Engineering responsibilities:
- Load and follow lassi-x-fp-error-diagnose and lassi-x-fp16-compensate before selecting a
  technique. If elementary functions are implicated, also use lassi-x-elementary-function-audit.
- Preserve the original C/C++ program's FP64 semantics and the module contract.
- Ensure the intervention collapses to base behavior at FP32; compensation must not conceal an
  algorithmic translation error or create a different high-precision algorithm.
- Respect the intersection of declared backend capabilities. Never assume FP32 operations exist
  merely because one backend exposes them.
- Edit only the named target copy, byte-compile it, and report the technique honestly.

Never weaken validators, change tolerances, read or embed oracle output, return constants, or
claim an improvement that was not measured. A comment-only, formatting-only, metadata-only, or
otherwise no-op edit is not compensation.

Workspace access: your only access to files and commands is the assigned workspace
toolset (list_resources, run_command, write_file, read_file, list_files). All paths
are workspace-relative. Call list_resources when choosing where to run commands."""


TECHNIQUE_SUMMARY = {
    "fp32-accumulate": "Accumulate low-precision reductions in FP32.",
    "blocked-fp32": "Sum low-precision blocks and combine block totals in FP32.",
    "pairwise": "Tree reduction for backends lacking an optimized reduction.",
    "kahan": "Sequential compensated summation for manual reductions.",
    "neumaier": "Kahan-Neumaier summation for mixed magnitudes and signs.",
    "double-word": "Two target-format words for a more accurate manual sum.",
    "double-word-fp32": "Two FP32 words for approximately FP64-grade manual sums.",
    "zero-center": "Store deviations from a known baseline.",
    "scaling": "Power-of-two scaling to avoid overflow and underflow.",
    "equilibrate": "Scale matrix rows and columns to use the target range more evenly.",
    "mixed-refine": "Low-precision operator with high-precision residual/state correction.",
    "precision-ramp": "Increase precision as a convergent iteration approaches its solution.",
    "residual-carry": "Carry discarded state updates forward as an explicit residual.",
    "ozaki-split": "Split matrix operands into low-precision words and combine products.",
    "stable-reformulation": "Use an algebraically equivalent, numerically stable formulation.",
    "stochastic-round": "Mode-1 stochastic casts at explicit long-term drift points.",
}


@dataclass(slots=True)
class CompensationVariant:
    """Record one agent-generated low-precision compensation variant.

    Attributes:
        candidate_id: Identifier of the base arena candidate.
        variant_id: Unique identifier for this compensated implementation.
        backend: Scope marker; portable variants use ``"portable"``.
        target_backends: Backends whose weak measurements motivated the shared change.
        guard_backends: Already-healthy backends on which the change must not regress.
        precision: Low precision whose error the variant attempts to reduce.
        technique: Selected compensation technique or provisional state.
        module_path: Path to the copied candidate module edited by the agent.
        status: Final validation status of the variant.
        correction_rounds: Number of diagnosis-driven repairs requested.
        diagnostics: Validator failures accumulated across attempts.
        usage: Aggregate model tokens and estimated cost.

    """

    candidate_id: str
    variant_id: str
    backend: str
    precision: str
    technique: str
    module_path: Path
    status: Status = Status.CRASHED
    correction_rounds: int = 0
    diagnostics: list[Diagnostic] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    turn_outcomes: list[dict[str, str | bool | int]] = field(default_factory=list)
    target_measurements: list[Measurement] = field(default_factory=list)
    target_backends: list[str] = field(default_factory=list)
    guard_backends: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the variant to a JSON-serializable artifact record.

        Returns:
            Dictionary with normalized string values for paths and status.

        """
        data = asdict(self)
        data["module_path"] = str(self.module_path)
        data["status"] = self.status.value
        data["target_measurements"] = [
            measurement.to_dict() for measurement in self.target_measurements
        ]
        return data


def select_weak_points(
    measurements: list[Measurement],
    *,
    error_threshold: float | None = 1e-2,
    error_metric: str = "max_rel_error",
    comparison_scope: str = "same_candidate",
) -> list[Measurement]:
    """Select low-precision measurements that merit agent compensation.

    Compiler/runtime crashes, unsupported, no-fit, and timed-out cells are excluded because
    they belong to accelerator qualification rather than numerical compensation. Numerically
    diverged measurements and successful points above the configured error threshold are weak.
    Domination is
    scoped to the same candidate by default so a losing candidate is not compensated merely
    because a different candidate is better. Cross-candidate comparison remains available as
    an explicit exploratory policy. At most one point is returned per candidate/backend/cell.

    Args:
        measurements: Base-candidate measurements from all configured precision cells.
        error_threshold: Absolute cutoff applied to the measurement's selected error metric.
            ``None`` disables threshold selection while retaining failure and domination rules.
        error_metric: Measurement attribute used for both threshold and domination selection.
        comparison_scope: ``"same_candidate"`` or explicitly ``"cross_candidate"``.

    Returns:
        Deduplicated FP16/BF16 measurements selected for compensation.

    """
    low = [point for point in measurements if point.precision in {"fp16", "bf16"}]
    weak: list[Measurement] = []
    for point in low:
        if point.status in {
            Status.CRASHED,
            Status.UNSUPPORTED,
            Status.NO_FIT,
            Status.TIMEOUT,
        }:
            continue
        if point.status != Status.OK or point.latency_s is None or point.y_error is None:
            weak.append(point)
            continue
        selected_error = getattr(point, error_metric, None)
        if selected_error is None:
            weak.append(point)
            continue
        if (
            error_threshold is not None
            and selected_error is not None
            and float(selected_error) > error_threshold
        ):
            weak.append(point)
            continue
        point_error = selected_error
        peers = [
            other
            for other in low
            if other.backend == point.backend
            and other.precision == point.precision
            and (comparison_scope == "cross_candidate" or other.candidate_id == point.candidate_id)
            and other.status == Status.OK
            and other.latency_s is not None
            and getattr(other, error_metric, None) is not None
            and other is not point
        ]
        dominated = False
        for other in peers:
            assert point.latency_s is not None
            assert other.latency_s is not None
            other_error = getattr(other, error_metric)
            assert other_error is not None
            if (
                other.latency_s <= point.latency_s
                and other_error <= point_error
                and (other.latency_s < point.latency_s or other_error < point_error)
            ):
                dominated = True
                break
        if dominated:
            weak.append(point)
    # One weak cell per base candidate/backend/precision.
    unique: dict[tuple[str, str, str], Measurement] = {}
    for point in weak:
        unique.setdefault((point.candidate_id, point.backend, point.precision), point)
    return list(unique.values())


def group_portable_weak_points(
    measurements: list[Measurement],
) -> list[list[Measurement]]:
    """Group target observations that should share one numerical source variant.

    Compatibility remains target-specific, but numerical changes are generated once per
    candidate and low-precision family. Backend measurements in a group are all presented to
    one persistent agent session and must all improve for the source variant to be promoted.
    """

    groups: dict[tuple[str, str], list[Measurement]] = {}
    for point in measurements:
        groups.setdefault((point.candidate_id, point.precision), []).append(point)
    return [groups[key] for key in sorted(groups)]


def _semantic_fingerprint(path: Path) -> str:
    """Return an AST fingerprint that ignores comments and source formatting.

    Args:
        path: Python module to parse.

    Returns:
        Stable structural representation of the module's Python syntax tree.

    Raises:
        OSError: If the source cannot be read.
        SyntaxError: If it is not valid Python.

    """
    tree = ast.parse(path.read_text())

    class CosmeticStripper(ast.NodeTransformer):
        """Remove declarations that do not affect candidate computation."""

        @staticmethod
        def _without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                return body[1:]
            return body

        def visit_Module(self, node: ast.Module) -> ast.AST:  # noqa: N802
            node.body = self._without_docstring(node.body)
            node.body = [
                statement
                for statement in node.body
                if not (
                    isinstance(statement, (ast.Assign, ast.AnnAssign))
                    and any(
                        isinstance(target, ast.Name) and target.id == "LASSI_PRECISION"
                        for target in (
                            statement.targets
                            if isinstance(statement, ast.Assign)
                            else [statement.target]
                        )
                    )
                )
            ]
            return self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802
            node.body = self._without_docstring(node.body)
            return self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:  # noqa: N802
            node.body = self._without_docstring(node.body)
            return self.generic_visit(node)

    stripped = CosmeticStripper().visit(tree)
    return ast.dump(stripped, include_attributes=False)


def _parse_technique(text: str, allowed: list[str]) -> str:
    """Recover the compensation technique selected in an agent response.

    Args:
        text: Raw response expected to contain a JSON ``technique`` field.
        allowed: Technique names permitted by the current run configuration.

    Returns:
        An allowed technique found in structured or free-form output, otherwise
        ``"agent-selected"``.

    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
        chosen = str(parsed.get("technique") or "")
        if chosen in allowed:
            return chosen
    except (json.JSONDecodeError, AttributeError):
        pass
    for technique in allowed:
        if technique in text:
            return technique
    return "agent-selected"


def _backend_capabilities(spec: BackendConfig) -> str:
    """Describe backend precision behavior for the compensation agent.

    Args:
        spec: Backend configuration and optional explicit capability declaration.

    Returns:
        A compact JSON or prose description suitable for inclusion in a model prompt.

    """
    if spec.capabilities is not None:
        return json.dumps(spec.capabilities.model_dump(mode="json"), sort_keys=True)
    if spec.type == "groq":
        return (
            "Storage/elementwise precision is FP16; do not assume explicit FP32 tensor "
            "operations. Matrix accumulation may be wider but is not directly controllable."
        )
    return (
        f"Torch device {getattr(spec, 'device', None)}; requested precisions={spec.precisions}. "
        "Explicit FP32 tensor operations are available."
    )


async def generate_compensation(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
    execution: ExecutionContext,
    base: Candidate,
    weak_points: list[Measurement],
    backends: Sequence[BackendConfig],
    target_backends: dict[str, Backend[Any]] | None = None,
    guard_points: list[Measurement] | None = None,
) -> CompensationVariant:
    """Generate one portable numerical variant for a candidate/precision family.

    The base module is copied into an isolated variant workspace before an agent chooses
    and implements one permitted technique. Every attempt is gated against both the
    authoritative C/C++ FP64 oracle and the requirement that compensation collapse to
    base behavior at FP32. When target backends are available, every weak cell in the group
    must improve. Validation failures are returned to the same persistent agent session for
    bounded correction rounds.

    Args:
        config: Validated run configuration and compensation policy.
        oracle: Authoritative output produced from the original C/C++ reference.
        run_dir: Root artifact directory for the current pipeline run.
        execution: Running execution context serving workspace tool calls.
        base: Semantically valid arena candidate to copy and compensate.
        weak_points: Same-candidate, same-precision observations motivating this variant.
        backends: Backend capability declarations for every motivating observation.
        target_backends: Runtime backends used for deterministic cross-platform feedback.
        guard_points: Healthy same-family cells that must remain non-regressed.

    Returns:
        Compensation record containing the selected technique, status, diagnostics,
        usage, correction count, and generated module path.

    Raises:
        OSError: If the variant workspace or initial candidate copy cannot be created.

    """
    if not weak_points:
        raise ValueError("portable compensation requires at least one weak measurement")
    precision = weak_points[0].precision
    if any(
        point.candidate_id != base.candidate_id or point.precision != precision
        for point in weak_points
    ):
        raise ValueError("portable compensation groups must share candidate and precision")
    guards = guard_points or []
    observations = [*weak_points, *guards]
    if any(
        point.candidate_id != base.candidate_id or point.precision != precision for point in guards
    ):
        raise ValueError("portable compensation guards must share candidate and precision")
    backend_by_name = {backend.name: backend for backend in backends}
    missing_backends = sorted({point.backend for point in observations} - set(backend_by_name))
    if missing_backends:
        raise ValueError(
            "portable compensation is missing backend declarations: " + ", ".join(missing_backends)
        )
    if target_backends is not None:
        missing_runtime = sorted({point.backend for point in observations} - set(target_backends))
        if missing_runtime:
            raise ValueError(
                "portable compensation is missing runtime backends: " + ", ".join(missing_runtime)
            )
    raw_slug = f"n-{base.candidate_id}-{precision}"
    slug = workspace_slug(raw_slug)
    mirror = execution.workspace_dir(slug)
    mirror.mkdir(parents=True, exist_ok=True)
    toolset = execution.register_workspace(slug)
    target = mirror / "candidate.py"
    await execution.stage_bytes(slug, "candidate.py", base.module_path.read_bytes())
    fixture = fixture_relative_path(config)
    if fixture is not None and config.oracle.input_fixture is not None:
        await execution.stage_bytes(
            slug,
            fixture,
            config.resolve_project_path(config.oracle.input_fixture).read_bytes(),
        )
    allowed = [name for name in config.compensation.techniques if name in TECHNIQUE_SUMMARY]
    variant = CompensationVariant(
        candidate_id=base.candidate_id,
        variant_id=slug,
        backend="portable",
        precision=precision,
        technique="pending",
        module_path=target,
        target_backends=sorted({point.backend for point in weak_points}),
        guard_backends=sorted({point.backend for point in guards}),
    )
    technique_text = "\n".join(f"- {name}: {TECHNIQUE_SUMMARY[name]}" for name in allowed)
    weak_ids = {id(point) for point in weak_points}
    evidence = "\n".join(
        (
            f"- {'weak' if id(point) in weak_ids else 'healthy guard'} "
            f"{point.backend}/{point.precision}: status={point.status.value}, "
            f"{config.pareto_error_metric}={getattr(point, config.pareto_error_metric, None)}, "
            f"max_abs={point.max_abs_error}, max_rel={point.max_rel_error}, "
            f"relative_l2={point.relative_l2}, invariant={point.invariant_error}, "
            f"notes={point.notes or 'none'}"
        )
        for point in observations
    )
    capabilities = "\n".join(
        f"- {name}: {_backend_capabilities(backend_by_name[name])}"
        for name in sorted({point.backend for point in observations})
    )
    prompt = f"""Create one portable correction for these weak low-precision observations.

Workspace toolset: {toolset} (all paths below are workspace-relative)
Target copy to edit: candidate.py (already contains the validated base translation)
Target precision family: {precision}
Configured error objective: {config.pareto_error_metric}

Observed target evidence:
{evidence}

Backend capability intersection (the change must respect every entry):
{capabilities}

Allowed techniques:
{technique_text}

Choose one primary technique suited to the shared failure and portable across these backends.
Edit the target copy. Do not add target-name conditionals or platform-specific operator rewrites.
Import reusable arithmetic from lassi_x.precision where applicable. Update the module's
LASSI_PRECISION metadata honestly. High-precision behavior must remain equivalent to the
original C/C++ reference and the compensation must collapse to the base behavior at FP32.
Preserve support for both the `{config.kernel.validation_dataset}` CPU semantic-validation
dataset and the `{config.evaluation_dataset}` merged accelerator evaluation dataset.

After editing and byte-compiling the target, return JSON only:
{{"technique":"one allowed name","summary":"what changed"}}
"""
    session = HermesSession(
        config.models.compensation,
        cwd=mirror,
        system_prompt=COMPENSATION_SYSTEM,
        toolsets=["skills", toolset],
        role=f"compensation-{slug}",
        memory=config.memory,
    )
    try:
        turn = await session.send(prompt)
        record_turn(variant, turn)
        variant.technique = _parse_technique(turn.text, allowed)
        base_fingerprint = _semantic_fingerprint(base.module_path)
        execution_backend = execution.backend()
        for attempt in range(config.compensation.correction_rounds + 1):
            diagnostic_dir = attempt_diagnostic_dir(run_dir, "variants", slug, attempt)
            await execution.mirror_file(slug, "candidate.py")
            try:
                changed = _semantic_fingerprint(target) != base_fingerprint
            except (OSError, SyntaxError):
                changed = True
            diagnostic: Diagnostic | None
            if not changed:
                external = None
                collapse = None
                diagnostic = Diagnostic(
                    gate="compensation-change",
                    message=(
                        "compensation made no substantive source change; comments and "
                        "formatting do not qualify"
                    ),
                )
            else:
                external = await validate_candidate(
                    config, execution_backend, slug, oracle, diagnostic_dir
                )
                collapse = (
                    await validate_fp32_collapse(
                        config,
                        execution_backend,
                        base.candidate_id,
                        slug,
                        diagnostic_dir,
                    )
                    if external.ok
                    else None
                )
                diagnostic = external.diagnostic or (collapse.diagnostic if collapse else None)
            if external is not None and external.ok and collapse is not None and collapse.ok:
                if target_backends is None:
                    variant.status = Status.OK
                    await execution.mirror_file(slug, "candidate.py")
                    break
                measured_points = list(
                    await asyncio.gather(
                        *(
                            target_backends[weak.backend].measure(
                                config,
                                oracle,
                                target,
                                candidate_id=variant.candidate_id,
                                variant_id=variant.variant_id,
                                precision=variant.precision,
                                compensation=variant.technique,
                            )
                            for weak in observations
                        )
                    )
                )
                variant.target_measurements.extend(measured_points)
                failures = []
                for index, (weak, measured) in enumerate(
                    zip(observations, measured_points, strict=True)
                ):
                    base_error = getattr(weak, config.pareto_error_metric, None)
                    measured_error = getattr(measured, config.pareto_error_metric, None)
                    acceptable = (
                        measured.status == Status.OK
                        and measured_error is not None
                        and measured.evaluation_semantic_verified
                        and bool(measured.accuracy_source)
                        and (
                            base_error is None
                            or (
                                measured_error < base_error
                                if index < len(weak_points)
                                else measured_error <= base_error
                            )
                        )
                    )
                    if not acceptable:
                        requirement = (
                            "strict improvement" if index < len(weak_points) else "no regression"
                        )
                        failures.append(
                            f"{weak.backend}/{weak.precision}: base={base_error}, "
                            f"variant={measured_error}, status={measured.status.value}, "
                            f"required={requirement}, notes={measured.notes or 'none'}"
                        )
                if not failures:
                    variant.status = Status.OK
                    await execution.mirror_file(slug, "candidate.py")
                    break
                diagnostic = Diagnostic(
                    gate="compensation-effect",
                    message=(
                        f"portable variant did not improve {config.pareto_error_metric} "
                        "on every weak backend without regressing healthy peers:\n"
                        + "\n".join(failures)
                    ),
                )
            if diagnostic is None:
                diagnostic = Diagnostic(
                    gate="compensation", message="compensation validation failed"
                )
            variant.diagnostics.append(diagnostic)
            if attempt >= config.compensation.correction_rounds:
                variant.status = Status.REJECTED
                break
            variant.correction_rounds += 1
            repair = f"""Correction round {variant.correction_rounds}.
The compensation target candidate.py in your workspace failed:

{diagnostic.for_agent()}

Repair the target without changing tolerances, disabling compensation, or embedding oracle
data. Preserve the selected technique where feasible. Return a short summary.
"""
            turn = await session.send(repair)
            record_turn(variant, turn)
    except Exception as exc:
        variant.status = Status.CRASHED
        variant.diagnostics.append(
            Diagnostic(gate="compensation-agent", message=f"{type(exc).__name__}: {exc}")
        )
    finally:
        await session.close()
    return variant
