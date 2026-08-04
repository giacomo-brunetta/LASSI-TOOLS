from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from .hermes import HermesSession
from .types import Candidate, Diagnostic, Measurement, Status, Usage
from .validation import (
    OracleResult,
    fixture_relative_path,
    validate_candidate,
    validate_fp32_collapse,
)

if TYPE_CHECKING:
    from pathlib import Path

    from .config import BackendConfig, RunConfig
    from .execution import ExecutionContext

COMPENSATION_SYSTEM = """Role: senior numerical analyst specializing in low-precision
scientific computing and compensated arithmetic.

You own one already-correct PyTorch translation and must make a targeted FP16/BF16
intervention for the named backend. Diagnose the observed error, choose a technique whose
assumptions match the kernel and hardware, and implement a substantive change that improves
low-precision behavior without changing the underlying algorithm.

Engineering responsibilities:
- Load and follow the lassi-x-fp16-compensate skill before selecting a technique.
- Preserve the original C/C++ program's FP64 semantics and the module contract.
- Ensure the intervention collapses to base behavior at FP32; compensation must not conceal an
  algorithmic translation error or create a different high-precision algorithm.
- Respect declared backend capabilities. Never assume FP32 operations exist on a backend that
  does not expose them.
- Edit only the named target copy, byte-compile it, and report the technique honestly.

Never weaken validators, change tolerances, read or embed oracle output, return constants, or
claim an improvement that was not measured. A comment-only, formatting-only, metadata-only, or
otherwise no-op edit is not compensation.

Workspace access: your only access to files and commands is the assigned workspace
toolset (list_resources, run_command, write_file, read_file, list_files). All paths
are workspace-relative. Call list_resources when choosing where to run commands."""


TECHNIQUE_SUMMARY = {
    "fp32-accumulate": "Accumulate low-precision reductions in FP32.",
    "pairwise": "Tree reduction for backends lacking an optimized reduction.",
    "kahan": "Sequential compensated summation for manual reductions.",
    "neumaier": "Kahan-Neumaier summation for mixed magnitudes and signs.",
    "double-word": "Two FP16 words for approximately FP32-grade manual sums.",
    "double-word-fp32": "Two FP32 words for approximately FP64-grade manual sums.",
    "zero-center": "Store deviations from a known baseline.",
    "scaling": "Power-of-two scaling to avoid overflow and underflow.",
    "mixed-refine": "Low-precision operator with high-precision residual/state correction.",
    "stochastic-round": "Unbiased rounding for long-term drift control.",
}


@dataclass(slots=True)
class CompensationVariant:
    """Record one agent-generated low-precision compensation variant.

    Attributes:
        candidate_id: Identifier of the base arena candidate.
        variant_id: Unique identifier for this compensated implementation.
        backend: Measurement backend targeted by the compensation.
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

    def to_dict(self) -> dict[str, Any]:
        """Convert the variant to a JSON-serializable artifact record.

        Returns:
            Dictionary with normalized string values for paths and status.

        """
        data = asdict(self)
        data["module_path"] = str(self.module_path)
        data["status"] = self.status.value
        return data


def select_weak_points(
    measurements: list[Measurement],
    *,
    error_threshold: float | None = 1e-2,
    error_metric: str = "max_rel_error",
    comparison_scope: str = "same_candidate",
) -> list[Measurement]:
    """Select low-precision measurements that merit agent compensation.

    Unsupported, no-fit, and timed-out cells are excluded because source-level
    numerical compensation cannot make those backends executable. Failed measurements
    and successful points above the configured error threshold are weak. Domination is
    scoped to the same candidate by default so a losing candidate is not compensated merely
    because a different candidate is better. Cross-candidate comparison remains available as
    an explicit exploratory policy. At most one point is returned per candidate/backend/cell.

    Args:
        measurements: Base-candidate measurements from all configured precision cells.
        error_threshold: Absolute cutoff applied to the measurement's selected error metric.
            ``None`` disables threshold selection while retaining failure and domination rules.
        error_metric: Measurement attribute compared with ``error_threshold``.
        comparison_scope: ``"same_candidate"`` or explicitly ``"cross_candidate"``.

    Returns:
        Deduplicated FP16/BF16 measurements selected for compensation.

    """
    low = [point for point in measurements if point.precision in {"fp16", "bf16"}]
    weak: list[Measurement] = []
    for point in low:
        if point.status in {Status.UNSUPPORTED, Status.NO_FIT, Status.TIMEOUT}:
            continue
        if point.status != Status.OK or point.latency_s is None or point.y_error is None:
            weak.append(point)
            continue
        selected_error = getattr(point, error_metric, None)
        if (
            error_threshold is not None
            and selected_error is not None
            and float(selected_error) > error_threshold
        ):
            weak.append(point)
            continue
        peers = [
            other
            for other in low
            if other.backend == point.backend
            and other.precision == point.precision
            and (comparison_scope == "cross_candidate" or other.candidate_id == point.candidate_id)
            and other.status == Status.OK
            and other.latency_s is not None
            and other.y_error is not None
            and other is not point
        ]
        dominated = False
        for other in peers:
            assert point.latency_s is not None
            assert point.y_error is not None
            assert other.latency_s is not None
            assert other.y_error is not None
            if (
                other.latency_s <= point.latency_s
                and other.y_error <= point.y_error
                and (other.latency_s < point.latency_s or other.y_error < point.y_error)
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
        f"Torch device {spec.device}; requested precisions={spec.precisions}. "
        "Explicit FP32 tensor operations are available."
    )


async def generate_compensation(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
    execution: ExecutionContext,
    base: Candidate,
    weak: Measurement,
    backend: BackendConfig,
) -> CompensationVariant:
    """Generate and validate compensation for one weak low-precision point.

    The base module is copied into an isolated variant workspace before an agent chooses
    and implements one permitted technique. Every attempt is gated against both the
    authoritative C/C++ FP64 oracle and the requirement that compensation collapse to
    base behavior at FP32. Validation failures are returned to the same persistent agent
    session for bounded correction rounds.

    Args:
        config: Validated run configuration and compensation policy.
        oracle: Authoritative output produced from the original C/C++ reference.
        run_dir: Root artifact directory for the current pipeline run.
        execution: Running execution context serving workspace tool calls.
        base: Semantically valid arena candidate to copy and compensate.
        weak: Low-precision measurement motivating this variant.
        backend: Backend whose numerical capabilities constrain the implementation.

    Returns:
        Compensation record containing the selected technique, status, diagnostics,
        usage, correction count, and generated module path.

    Raises:
        OSError: If the variant workspace or initial candidate copy cannot be created.

    """
    raw_slug = f"{base.candidate_id}-{backend.name}-{weak.precision}"
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", raw_slug)
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
        backend=backend.name,
        precision=weak.precision,
        technique="pending",
        module_path=target,
    )
    technique_text = "\n".join(f"- {name}: {TECHNIQUE_SUMMARY[name]}" for name in allowed)
    prompt = f"""Compensate this weak low-precision point.

Workspace toolset: {toolset} (all paths below are workspace-relative)
Target copy to edit: candidate.py (already contains the validated base translation)
Backend: {backend.name}
Backend capabilities: {_backend_capabilities(backend)}
Target precision: {weak.precision}
Observed status: {weak.status.value}
Observed max relative error: {weak.max_rel_error}
Observed relative L2 error: {weak.relative_l2}
Observed notes: {weak.notes}

Allowed techniques:
{technique_text}

Choose one primary technique suited to the failure and backend. Edit the target copy.
Import reusable arithmetic from lassi_x.precision where applicable. Update the module's
LASSI_PRECISION metadata honestly. High-precision behavior must remain equivalent to the
original C/C++ reference and the compensation must collapse to the base behavior at FP32.
Preserve support for both the `{config.kernel.validation_dataset}` accuracy dataset and
the `{config.measure.performance_dataset}` performance dataset.

After editing and byte-compiling the target, return JSON only:
{{"technique":"one allowed name","summary":"what changed"}}
"""
    session = HermesSession(
        config.models.compensation,
        cwd=mirror,
        system_prompt=COMPENSATION_SYSTEM,
        toolsets=["skills", toolset],
        role=f"compensation-{slug}",
    )
    try:
        turn = await session.send(prompt)
        variant.usage.add(turn.usage)
        variant.turn_outcomes.append(
            {
                "completed": turn.completed,
                "exit_reason": turn.exit_reason,
                "attempts": turn.attempts,
            }
        )
        variant.technique = _parse_technique(turn.text, allowed)
        base_fingerprint = _semantic_fingerprint(base.module_path)
        execution_backend = execution.backend()
        for attempt in range(config.compensation.correction_rounds + 1):
            diagnostic_dir = run_dir / "diagnostics" / "variants" / slug / f"attempt-{attempt}"
            diagnostic_dir.mkdir(parents=True, exist_ok=True)
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
                variant.status = Status.OK
                await execution.mirror_file(slug, "candidate.py")
                break
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
            variant.usage.add(turn.usage)
            variant.turn_outcomes.append(
                {
                    "completed": turn.completed,
                    "exit_reason": turn.exit_reason,
                    "attempts": turn.attempts,
                }
            )
    except Exception as exc:
        variant.status = Status.CRASHED
        variant.diagnostics.append(
            Diagnostic(gate="compensation-agent", message=f"{type(exc).__name__}: {exc}")
        )
    finally:
        await session.close()
    return variant
