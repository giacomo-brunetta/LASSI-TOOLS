from __future__ import annotations

import json
from typing import Any


def json_response(
    verdict: str,
    confidence: float,
    summary: str,
    *,
    valid_verdicts: set[str],
    invalid_summary_prefix: str,
    round_confidence: int | None = None,
    metrics: dict[str, Any] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    counterexamples: list[dict[str, Any]] | None = None,
    logs: dict[str, str] | None = None,
) -> str:
    if verdict not in valid_verdicts:
        verdict = "ERROR"
        confidence = 0.0
        summary = f"{invalid_summary_prefix} Original summary: {summary}"

    confidence_value: float = float(confidence)
    if round_confidence is not None:
        confidence_value = round(confidence_value, round_confidence)

    payload: dict[str, Any] = {
        "verdict": verdict,
        "confidence": confidence_value,
        "summary": summary,
        "artifacts": artifacts or [],
        "metrics": metrics or {},
        "logs": logs or {"stdout": "", "stderr": ""},
    }
    if warnings is not None:
        payload["warnings"] = warnings
    if counterexamples is not None:
        payload["counterexamples"] = counterexamples

    return json.dumps(payload, indent=2, sort_keys=True)
