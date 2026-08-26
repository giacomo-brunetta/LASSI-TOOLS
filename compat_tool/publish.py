"""Publish one independent target compatibility snapshot and wiki."""

# ruff: noqa: TC003

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from compat_tool.io import atomic_json, load_json, stable_hash

COMPLETE_STATUSES = {"compiled", "compile_rejected", "not_applicable"}


def _page(op_name: str, entry: dict[str, Any], snapshot: dict[str, Any]) -> str:
    target = snapshot["target"]
    lines = [
        f"# {op_name}",
        "",
        f"- Target: `{target['target_id']}`",
        f"- Family: `{target['family']}`",
        f"- Compiler: `{snapshot['provenance'].get('compiler', 'unknown')}`",
        f"- Inventory revision: `{snapshot['source'].get('revision', 'unknown')}`",
    ]
    if not entry["included"]:
        lines.extend(["- Status: excluded", f"- Reason: {entry['exclusion_reason']}", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "",
            "## Canonical compile cases",
            "",
            "| Precision | Status | Input | Diagnostic |",
            "|---|---|---|---|",
        ]
    )
    for precision, cases in entry["cases"].items():
        for case_name, case in cases.items():
            result = case["result"]
            input_spec = str(
                result.get("input_spec") or case["fixture"]["validation"].get("input_spec") or "—"
            ).replace("|", "\\|")
            diagnostic = str(result.get("error") or "—").replace("|", "\\|").replace("\n", " ")
            if len(diagnostic) > 500:
                diagnostic = diagnostic[:497] + "..."
            row = (
                f"| `{precision}` / `{case_name}` | `{result['status']}` | "
                f"{input_spec} | {diagnostic} |"
            )
            lines.append(row)
    lines.extend(
        [
            "",
            "> `compiled` applies only to the named case, precision, target, and compiler "
            "snapshot. It is not a runtime-correctness or performance result.",
            "",
        ]
    )
    return "\n".join(lines)


def build_snapshot(manifest: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    if manifest["manifest_hash"] != probe["manifest_hash"]:
        raise ValueError("probe results were produced from a different manifest")
    operators: dict[str, Any] = {}
    missing_results = 0
    incomplete_results = 0
    for op_name, record in sorted(manifest["operators"].items()):
        entry: dict[str, Any] = {
            "included": record["included"],
            "exclusion_reason": record["exclusion_reason"],
            "metadata": record["metadata"],
            "cases": {},
        }
        if record["included"]:
            for precision in probe["target"]["precisions"]:
                published_cases: dict[str, Any] = {}
                for case_name, fixture in record["cases"][precision].items():
                    key = f"{op_name}|{precision}|{case_name}"
                    result = probe["results"].get(key)
                    if result is None:
                        missing_results += 1
                        result = {"status": "environment_error", "error": "probe result is missing"}
                    if result.get("status") not in COMPLETE_STATUSES:
                        incomplete_results += 1
                    published_cases[case_name] = {"fixture": fixture, "result": result}
                entry["cases"][precision] = published_cases
        operators[op_name] = entry

    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "kind": "target-compatibility-snapshot",
        "target": probe["target"],
        "source": manifest["source"],
        "manifest_hash": manifest["manifest_hash"],
        "target_hash": probe["target_hash"],
        "generated_at": datetime.now(UTC).isoformat(),
        "provenance": probe.get("environment") or {},
        "operators": operators,
        "complete": missing_results == 0 and incomplete_results == 0,
        "summary": {
            "operators": len(operators),
            "included": sum(bool(item["included"]) for item in operators.values()),
            "excluded": sum(not bool(item["included"]) for item in operators.values()),
            "missing_results": missing_results,
            "incomplete_results": incomplete_results,
        },
    }
    snapshot["snapshot_hash"] = stable_hash(snapshot)
    return snapshot


def publish_snapshot(
    manifest_path: Path,
    results_path: Path,
    output_root: Path,
) -> tuple[dict[str, Any], Path, Path]:
    snapshot = build_snapshot(load_json(manifest_path), load_json(results_path))
    target_id = str(snapshot["target"]["target_id"])
    snapshot_path = output_root / "snapshots" / target_id / "snapshot.json"
    wiki_path = output_root / "wiki" / target_id
    temporary = wiki_path.with_name(f".{target_id}.{os.getpid()}.tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    for op_name, entry in snapshot["operators"].items():
        (temporary / f"{op_name}.md").write_text(_page(op_name, entry, snapshot), encoding="utf-8")
    if wiki_path.exists():
        shutil.rmtree(wiki_path)
    os.replace(temporary, wiki_path)
    atomic_json(snapshot_path, snapshot)
    return snapshot, snapshot_path, wiki_path
