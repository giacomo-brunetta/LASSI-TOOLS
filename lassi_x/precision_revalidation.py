"""Plan evaluation-only recovery without rewriting historical results or regenerating code."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from .types import Measurement

if TYPE_CHECKING:
    from pathlib import Path


def plan_revalidation(campaign: Path) -> dict[str, Any]:
    import json  # noqa: PLC0415

    summary: Counter[str] = Counter()
    targets: dict[tuple[str, ...], dict[str, Any]] = {}
    records = (
        [campaign]
        if campaign.is_file()
        else sorted((campaign / "runs").glob("*/*/run.json"))
        if (campaign / "runs").is_dir()
        else sorted(campaign.rglob("run.json"))
    )
    for path in records:
        if "legacy" in path.parts or "quota-retry-history" in path.parts:
            continue
        record = json.loads(path.read_text())
        for raw in record.get("measurements", []):
            point = Measurement.from_dict(raw)
            if point.precision == "fp64":
                summary["high_precision_controls_preserved"] += 1
                continue
            summary["precision_observations_preserved"] += 1
            summary[point.precision_verdict] += 1
            if point.precision_eligible or point.precision_verdict == "failed":
                continue
            config = str(record.get("config_path") or "")
            oracle = str(record.get("oracle", {}).get("output_path") or "")
            key = (
                point.module_path,
                point.source_hash,
                point.backend,
                point.precision,
                point.evaluation_dataset,
                config,
                oracle,
            )
            target = targets.setdefault(
                key,
                {
                    "module": point.module_path,
                    "original_source_hash": point.source_hash,
                    "backend": point.backend,
                    "precision": point.precision,
                    "dataset": point.evaluation_dataset,
                    "config": config,
                    "action": "measure_saved_source_only",
                    "original_observations": [],
                    "command": [
                        "lassi-x",
                        "precision",
                        "measure",
                        "--config",
                        config,
                        "--module",
                        point.module_path,
                        "--backend",
                        point.backend,
                        "--precision",
                        point.precision,
                    ],
                },
            )
            target["original_observations"].append(
                {
                    "record": str(path),
                    "candidate": point.candidate_id,
                    "variant": point.variant_id,
                    "status": point.status.value,
                }
            )
    return {
        "policy": "executed-dtype-v3",
        "campaign": str(campaign),
        "raw_results_modified": False,
        "model_calls_required": 0,
        "note": "Plan only. Missing evidence is unverified, never a retroactive model failure. "
        "Recheck source hashes before executing; keep new measurements separate from old ones.",
        "summary": dict(summary),
        "targets": list(targets.values()),
    }
