from __future__ import annotations

import ast
import asyncio
import json
import re
import time
import weakref
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .agent_support import (
    BOUNDED_TOOL_OUTPUT_POLICY,
    attempt_diagnostic_dir,
    record_turn,
    workspace_slug,
)
from .hermes import HermesSession
from .precision_policy import precision_contract
from .repair_history import (
    RepairHistory,
    RepairProposalError,
    digest,
    input_contract,
    parse_hypothesis,
)
from .types import Candidate, Diagnostic, Measurement, Status, Usage
from .validation import (
    OracleResult,
    fixture_relative_path,
    validate_candidate,
    validate_fp32_collapse,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

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
are workspace-relative. Call list_resources when choosing where to run commands.""" + (
    BOUNDED_TOOL_OUTPUT_POLICY
)


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
    hypothesis: dict[str, str] = field(default_factory=dict)
    history_scope: str = ""
    attempt_history: list[dict[str, Any]] = field(default_factory=list)
    baseline_errors: dict[str, float | None] = field(default_factory=dict)
    repair_model: str = ""
    arithmetic_policy: str = "target_format_only"
    elapsed_s: float = 0.0
    first_improvement_s: float | None = None
    first_improvement_tokens: int | None = None

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
        latest = {p.backend: p for p in self.target_measurements}
        targets = [latest[name] for name in self.target_backends if name in latest]
        data["target_precision_verified"] = bool(latest) and all(
            point.precision_eligible for point in latest.values()
        )
        data["stable_success"] = (
            self.status == Status.OK
            and bool(latest)
            and all(point.stable_success for point in latest.values())
        )
        data["accuracy_improved"] = (
            self.status == Status.OK
            and bool(targets)
            and len(targets) == len(self.target_backends)
            and all(
                p.precision_eligible
                and p.y_error is not None
                and (
                    (baseline_error := self.baseline_errors.get(name)) is None
                    or p.y_error < baseline_error
                )
                for name, p in latest.items()
                if name in self.target_backends
            )
        )
        data["recovered"] = (
            self.status == Status.OK
            and bool(latest)
            and all(p.stable_success for p in latest.values())
        )
        data["arithmetic_classes"] = sorted({p.arithmetic_class for p in latest.values()})
        data["error_reduction_factors"] = {
            name: baseline / p.y_error
            if p.y_error is not None and p.y_error > 0 and baseline is not None
            else None
            for name, p in latest.items()
            if (baseline := self.baseline_errors.get(name)) is not None
        }
        return data

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CompensationVariant:
        data = dict(value)
        data.pop("target_precision_verified", None)
        data.pop("stable_success", None)
        for derived in (
            "accuracy_improved",
            "recovered",
            "arithmetic_classes",
            "error_reduction_factors",
        ):
            data.pop(derived, None)
        data["module_path"] = Path(data["module_path"])
        data["status"] = Status(data["status"])
        data["diagnostics"] = [Diagnostic.from_dict(item) for item in data["diagnostics"]]
        data["usage"] = Usage.from_dict(data["usage"])
        data["target_measurements"] = [
            Measurement.from_dict(item) for item in data["target_measurements"]
        ]
        return cls(**data)


def select_weak_points(
    measurements: list[Measurement],
    *,
    error_threshold: float | None = 1e-2,
    error_metric: str = "max_rel_error",
    comparison_scope: str = "same_candidate",
    include_catastrophic: bool = False,
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
        if not point.precision_eligible:
            continue
        if point.numerically_catastrophic and not include_catastrophic:
            continue
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
            and other.arithmetic_class == point.arithmetic_class
            and (comparison_scope == "cross_candidate" or other.candidate_id == point.candidate_id)
            and other.status == Status.OK
            and other.precision_eligible
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


def _valid_python(path: Path) -> bool:
    try:
        ast.parse(path.read_text())
        return True
    except (OSError, SyntaxError):
        return False


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


_HISTORY_LOCKS: weakref.WeakKeyDictionary[Any, dict[str, asyncio.Lock]] = (
    weakref.WeakKeyDictionary()
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
    *,
    previous: CompensationVariant | None = None,
) -> CompensationVariant:
    """Serialize same-arm/kernel attempts so every next agent sees completed history."""
    locks = _HISTORY_LOCKS.setdefault(asyncio.get_running_loop(), {})
    key = json.dumps(
        [
            str(config.compensation.history_dir or run_dir / "repair-history"),
            config.kernel.name,
            config.models.compensation.model_dump(mode="json"),
            config.compensation.arithmetic_policy,
        ],
        sort_keys=True,
        default=str,
    )
    async with locks.setdefault(key, asyncio.Lock()):
        return await _generate_compensation(
            config,
            oracle,
            run_dir,
            execution,
            base,
            weak_points,
            backends,
            target_backends,
            guard_points,
            previous=previous,
        )


async def _generate_compensation(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
    execution: ExecutionContext,
    base: Candidate,
    weak_points: list[Measurement],
    backends: Sequence[BackendConfig],
    target_backends: dict[str, Backend[Any]] | None = None,
    guard_points: list[Measurement] | None = None,
    *,
    previous: CompensationVariant | None = None,
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
    started = time.perf_counter()
    config = config.model_copy(deep=True)
    config.compensation.frozen_reference = base.module_path
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
    baseline_bytes = base.module_path.read_bytes()
    contract = (
        input_contract(baseline_bytes.decode()) if config.compensation.freeze_input_builder else ""
    )
    scope_files = [config.kernel.reference, *config.kernel.context]
    if config.oracle.input_fixture:
        scope_files.append(config.oracle.input_fixture)
    history = RepairHistory(
        config.compensation.history_dir or run_dir / "repair-history",
        {
            "kernel": config.kernel.name,
            "model_arm": config.models.compensation.model_dump(mode="json"),
            "policy": config.compensation.arithmetic_policy,
            "validation_dataset": config.kernel.validation_dataset,
            "evaluation_dataset": config.evaluation_dataset,
            "oracle": config.oracle.model_dump(mode="json"),
            "equivalence": config.arena.equivalence.model_dump(mode="json"),
            "references": {
                str(p): digest(config.resolve_project_path(p).read_bytes())
                if config.resolve_project_path(p).is_file()
                else "missing"
                for p in scope_files
            },
        },
    )
    if not any(
        e.get("kind") == "baseline" and e["source_sha256"] == digest(baseline_bytes)
        for e in history.entries()
    ):
        history.record(baseline_bytes, {"kind": "baseline", "candidate_id": base.candidate_id})
    has_saved_edit = previous is not None and previous.module_path.is_file()
    source = (
        previous.module_path.read_bytes()
        if previous is not None and has_saved_edit
        else baseline_bytes
    )
    await execution.stage_bytes(slug, "candidate.py", source)
    ledger = history.entries()
    for entry in ledger:
        await execution.stage_bytes(
            slug,
            "history/" + entry["source_file"],
            (history.root / entry["source_file"]).read_bytes(),
        )
    compact_ledger = [
        {
            **{
                key: entry.get(key)
                for key in (
                    "event_id",
                    "kind",
                    "candidate_id",
                    "precision",
                    "source_file",
                    "hypothesis",
                    "status",
                )
            },
            "diagnostics": entry.get("diagnostics", [entry.get("diagnostic", "")])[-1:],
            "measurements": [
                {
                    key: point.get(key)
                    for key in (
                        "backend",
                        "precision",
                        "relative_l2",
                        "latency_s",
                        "arithmetic_class",
                        "precision_verdict",
                    )
                }
                for point in entry.get("measurements", [])
            ],
        }
        for entry in ledger
    ]
    await execution.stage_bytes(
        slug, "history/ledger.json", json.dumps(compact_ledger, default=str).encode()
    )
    fixture = fixture_relative_path(config)
    if fixture is not None and config.oracle.input_fixture is not None:
        await execution.stage_bytes(
            slug,
            fixture,
            config.resolve_project_path(config.oracle.input_fixture).read_bytes(),
        )
    forbidden = (
        {"fp32-accumulate", "blocked-fp32", "double-word-fp32", "mixed-refine", "precision-ramp"}
        if config.compensation.arithmetic_policy == "target_format_only"
        else {"double-word-fp32", "mixed-refine", "precision-ramp"}
    )
    allowed = [
        name
        for name in config.compensation.techniques
        if name in TECHNIQUE_SUMMARY and name not in forbidden
    ]
    variant = CompensationVariant(
        candidate_id=base.candidate_id,
        variant_id=slug,
        backend="portable",
        precision=precision,
        technique="pending",
        module_path=target,
        target_backends=sorted({point.backend for point in weak_points}),
        guard_backends=sorted({point.backend for point in guards}),
        history_scope=str(history.root),
        baseline_errors={p.backend: p.y_error for p in weak_points},
        repair_model=config.models.compensation.model,
        arithmetic_policy=config.compensation.arithmetic_policy,
    )
    technique_text = "\n".join(f"- {name}: {TECHNIQUE_SUMMARY[name]}" for name in allowed)
    if previous is not None:
        variant.first_improvement_s = previous.first_improvement_s
        variant.first_improvement_tokens = previous.first_improvement_tokens
        variant.hypothesis = dict(previous.hypothesis)
        variant.attempt_history.extend(previous.attempt_history)
        variant.technique = previous.technique
        variant.usage.add(previous.usage)
        variant.turn_outcomes.extend(previous.turn_outcomes)
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
History: history/ledger.json and history/*.py contain this kernel's own model-arm attempts,
including other candidates and FP16/BF16. Other models' and kernels' repairs are not provided.
Consult their failure diagnostics and measured outcomes; do not repeat failed strategies by
renaming them. A justified revision needs a specific new hypothesis and revisit_reason.
Frozen input contract: do not edit build_inputs, its dependencies, input encoding, dimensions,
or initialization. All target evaluation uses the original baseline's supplied inputs.

{precision_contract(config)}

Prefer one dtype-generic source intervention that can be independently tested in both FP16
and BF16. Do not assume that success in either format establishes success in the other.
The current session is scored only against its explicitly supplied target and guard cells.

Observed target evidence:
{evidence}

Backend capability intersection (the change must respect every entry):
{capabilities}

Allowed techniques:
{technique_text}

Choose one primary technique suited to the shared failure and portable across these backends.
Edit the target copy. Do not add target-name conditionals or platform-specific operator rewrites.
Import reusable arithmetic from lassi_x.precision where applicable.
Under target_format_only use only target-format helpers: pairwise, Kahan, Neumaier,
or double-word with the default component dtype. Generic mixed-precision scaling,
centering, residual-carry and splitting templates are not compliant implementations;
the technique names permit a target-format rewrite, not importing the mixed template.
Update LASSI_PRECISION metadata honestly. High-precision behavior must remain equivalent to the
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
        memory=config.memory.model_copy(update={"enabled": False}),
    )
    try:
        if previous is None or not has_saved_edit:
            if config.compensation.require_hypothesis:
                planning = (
                    prompt.split("After editing and byte-compiling")[0]
                    + """
PLAN ONLY: do not edit candidate.py yet. Diagnose the error and propose a distinct repair.
Return JSON only with nonempty strings: technique, failure_mechanism, transformation,
semantics_argument, arithmetic_plan, strategy_key, novelty, and optional revisit_reason.
strategy_key identifies mechanism AND operation location, not just the technique name.
Explain a new hypothesis when revisiting a mechanism. Wider state or whole-kernel promotion
is forbidden in both tracks. Mixed accumulation requires the named backend allowlist.
"""
                )
                turn = await session.send(planning)
                record_turn(variant, turn)
                variant.hypothesis = parse_hypothesis(turn.text, allowed)
                variant.technique = variant.hypothesis["technique"]
                history.reject_repetition(variant.hypothesis)
                await execution.mirror_file(slug, "candidate.py")
                if target.read_bytes() != source:
                    raise RepairProposalError(
                        "planning phase edited candidate.py before hypothesis approval"
                    )
                prompt += "\nApproved hypothesis:\n" + json.dumps(variant.hypothesis)
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
            input_changed = False
            try:
                input_changed = bool(contract) and input_contract(target.read_text()) != contract
                repeated = history.repeated_source(digest(_semantic_fingerprint(target).encode()))
            except (OSError, SyntaxError, ValueError):
                input_changed, repeated = True, False
            if input_changed or (repeated and previous is None):
                external = collapse = None
                diagnostic = Diagnostic(
                    gate="repair-input-contract" if input_changed else "repair-repetition",
                    message="frozen input builder/dependencies changed"
                    if input_changed
                    else (
                        "implementation repeats an earlier attempt; "
                        "renaming a strategy is not novelty"
                    ),
                )
            elif not changed:
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
                # Refresh the authoritative baseline immediately before the check.
                # Imported CPU candidates need not exist in remote cN workspaces,
                # which may contain stale files from unrelated campaigns.
                await execution.stage_bytes(slug, ".lassi/baseline.py", baseline_bytes)
                collapse = (
                    await validate_fp32_collapse(
                        config,
                        execution_backend,
                        slug,
                        slug,
                        diagnostic_dir,
                        base_module=".lassi/baseline.py",
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
                        and measured.precision_eligible
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
                    if variant.first_improvement_s is None:
                        variant.first_improvement_s = (
                            time.perf_counter()
                            - started
                            + (previous.elapsed_s if previous else 0.0)
                        )
                        variant.first_improvement_tokens = (
                            variant.usage.input_tokens + variant.usage.output_tokens
                        )
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
            event = history.record(
                target.read_bytes(),
                {
                    "kind": "attempt",
                    "candidate_id": base.candidate_id,
                    "precision": precision,
                    "hypothesis": variant.hypothesis,
                    "semantic_fingerprint": digest(_semantic_fingerprint(target).encode())
                    if not input_changed
                    else "",
                    "status": "rejected",
                    "diagnostic": diagnostic.for_agent(),
                    "measurements": [p.to_dict() for p in variant.target_measurements],
                },
            )
            variant.attempt_history.append(event)
            if attempt >= config.compensation.correction_rounds:
                variant.status = Status.REJECTED
                break
            variant.correction_rounds += 1
            repair = f"""Correction round {variant.correction_rounds}.
The compensation target candidate.py in your workspace failed:

{diagnostic.for_agent()}

Repair the target without changing tolerances, disabling compensation, or embedding oracle
data. Preserve the selected technique where feasible. Do not print tensors, numerical artifacts,
or complete logs; use bounded summaries and artifact files. Return a short summary.
"""
            if previous is not None and not variant.turn_outcomes[len(previous.turn_outcomes) :]:
                repair = prompt + "\nRevalidation of your saved edit failed:\n" + repair
            turn = await session.send(repair)
            record_turn(variant, turn)
    except RepairProposalError as exc:
        variant.status = Status.REJECTED
        variant.diagnostics.append(Diagnostic(gate="repair-hypothesis", message=str(exc)))
    except Exception as exc:
        variant.status = Status.CRASHED
        variant.diagnostics.append(
            Diagnostic(gate="compensation-agent", message=f"{type(exc).__name__}: {exc}")
        )
    finally:
        variant.elapsed_s = (
            time.perf_counter() - started + (previous.elapsed_s if previous else 0.0)
        )
        await session.close()
        if target.is_file():
            variant.attempt_history.append(
                history.record(
                    target.read_bytes(),
                    {
                        "kind": "result",
                        "candidate_id": base.candidate_id,
                        "precision": precision,
                        "hypothesis": variant.hypothesis,
                        "status": variant.status.value,
                        "diagnostics": [d.for_agent() for d in variant.diagnostics],
                        "measurements": [p.to_dict() for p in variant.target_measurements],
                        "usage": asdict(variant.usage),
                        "elapsed_s": variant.elapsed_s,
                        "first_improvement_s": variant.first_improvement_s,
                        "first_improvement_tokens": variant.first_improvement_tokens,
                        "semantic_fingerprint": digest(_semantic_fingerprint(target).encode())
                        if _valid_python(target)
                        else "",
                    },
                )
            )
    return variant
