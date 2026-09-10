"""Typed final-run records and human-readable reporting."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Literal

from .config import StrictModel
from .pareto import valid_point
from .skills import AUTOMATION_SKILLS, install_root

if TYPE_CHECKING:
    from .config import RunConfig
    from .types import Measurement


class RunRecord(StrictModel):
    """Validated top-level schema persisted as ``run.json``."""

    schema_version: Literal[1] = 1
    status: Literal["ok", "partial", "failed"]
    kernel: str
    started_at: str
    finished_at: str
    wall_seconds: float
    config_path: str
    oracle: dict[str, Any]
    datasets: dict[str, Any]
    security: dict[str, Any]
    evaluation: dict[str, Any]
    skills: list[dict[str, str]]
    execution: dict[str, Any]
    planner: dict[str, Any]
    acceptance: dict[str, Any]
    pareto_error_metric: str
    accuracy: dict[str, Any]
    candidates: list[dict[str, Any]]
    compatibility_candidates: list[dict[str, Any]]
    numerical_candidates: list[dict[str, Any]]
    compensation_variants: list[dict[str, Any]]
    measurements: list[dict[str, Any]]
    frontier: list[dict[str, Any]]
    visualizations: dict[str, Any]


def skill_records() -> list[dict[str, str]]:
    """Fingerprint every installed automation skill used by a run."""

    root = install_root()
    manifest_path = root / ".lassi-x-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    bundle_version = str(manifest.get("lassi_x_version") or "unknown")
    return [
        {
            "name": name,
            "version": bundle_version,
            "sha256": hashlib.sha256((root / name / "SKILL.md").read_bytes()).hexdigest(),
        }
        for name in AUTOMATION_SKILLS
    ]


def render_summary(record: RunRecord) -> str:
    """Render the concise Markdown summary paired with ``run.json``."""

    lines = [
        f"# LASSI-X run: {record.kernel}",
        "",
        f"- Status: **{record.status}**",
        f"- Oracle: original C/C++ FP64 (`{record.oracle['output_path']}`)",
        f"- CPU semantic-validation dataset: `{record.datasets['cpu_validation']}`",
        f"- Accelerator accuracy/latency dataset: `{record.datasets['evaluation']}`",
        f"- Candidates generated: {len(record.candidates)}",
        "- Candidates passing FP64 reference validation: "
        f"{sum(candidate['status'] == 'ok' for candidate in record.candidates)}",
        f"- Accelerator repair variants: {len(record.compatibility_candidates)}",
        f"- Portable numerical attempts: {len(record.compensation_variants)}",
        f"- Promoted numerical trunks: {len(record.numerical_candidates)}",
        f"- Measurements: {len(record.measurements)}",
        f"- Frontier points: {len(record.frontier)}",
        "- Required accelerator backends satisfied: "
        f"{record.acceptance['satisfied']}/{record.acceptance['required']}",
        f"- Pareto plots: [overall]({record.visualizations['overall']['svg']})",
        "",
        "## Candidates",
        "",
    ]
    for candidate in record.candidates:
        lines.append(
            f"- `{candidate['candidate_id']}`: {candidate['status']}; "
            f"model={candidate['provider'] or 'ambient'}:{candidate['model']}; "
            f"corrections={candidate['correction_rounds']}"
        )
    lines += ["", "## Frontier", ""]
    for point in record.frontier:
        lines.append(
            f"- `{point['candidate_id']}/{point['variant_id']}` "
            f"{point['backend']} {point['precision']} {point['compensation']}: "
            f"latency={point['latency_s']} s, "
            f"{record.pareto_error_metric}={point.get(record.pareto_error_metric)}"
        )
    return "\n".join(lines) + "\n"


def evaluate_acceptance(
    config: RunConfig,
    measurements: list[Measurement],
) -> dict[str, Any]:
    """Evaluate explicit run-level backend and precision requirements."""

    required_backends = config.required_backends
    results: dict[str, dict[str, Any]] = {}
    for backend in required_backends:
        required_precisions = config.success.required_precisions.get(backend, [])
        valid = [
            point
            for point in measurements
            if point.backend == backend
            and valid_point(point)
            and point.evaluation_semantic_verified
            and bool(point.accuracy_source)
        ]
        passed_precisions = sorted({point.precision for point in valid})
        if required_precisions:
            missing = sorted(set(required_precisions) - set(passed_precisions))
            passed = not missing
        else:
            missing = []
            passed = bool(valid)
        results[backend] = {
            "passed": passed,
            "required_precisions": required_precisions,
            "passed_precisions": passed_precisions,
            "missing_precisions": missing,
        }
    satisfied = sum(item["passed"] for item in results.values())
    return {
        "policy": (
            "all_configured_accelerators"
            if config.success.required_backends is None
            else "explicit"
        ),
        "required_backends": required_backends,
        "required": len(required_backends),
        "satisfied": satisfied,
        "passed": satisfied == len(required_backends),
        "requires_device_accuracy_latency_pair": True,
        "backends": results,
    }
