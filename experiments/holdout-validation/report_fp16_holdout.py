"""Join complete paper FP16 coverage to source-bound holdout evidence."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

from lassi_x.holdout import read, sha, write


def collect(freeze: Path, results: Path, previous_results: Path, output: Path) -> dict:
    manifest = read(freeze / "manifest.json")
    coverage = read(freeze / "coverage.json")
    for name, digest in manifest["files"].items():
        if sha(freeze / name) != digest:
            raise ValueError(f"Freeze changed: {name}")
    new = read(results / "results.json") if (results / "results.json").exists() else {}
    old = read(previous_results / "results.json")
    targets, rows = [], []
    for entry in coverage:
        name = entry["target"]
        if entry["disposition"] == "reuse_unchanged_frozen_target":
            evidence_freeze = Path(entry["prior_freeze"])
            evidence_results = Path(entry.get("prior_results", previous_results))
            data = (
                old
                if evidence_results == previous_results
                else read(evidence_results / "results.json")
            ).get(name)
        else:
            evidence_freeze, data, evidence_results = freeze, new.get(name), results
        evidence_manifest = read(evidence_freeze / "manifest.json")
        folder = evidence_freeze / Path(name).parent
        if sha(folder / "repaired.py") != entry["source_sha256"]:
            raise ValueError(f"Paper source binding changed: {name}")
        row = {k: entry[k] for k in ("model", "kernel", "candidate", "precision", "selection")}
        row.update(
            repaired_source_sha256=entry["source_sha256"],
            baseline_source_sha256=sha(folder / "baseline.py"),
            evidence_manifest_sha256=sha(evidence_freeze / "manifest.json"),
            evidence_results=str(evidence_results),
            status="pending",
        )
        if data is not None:
            if data["completion"]["returncode"] not in (0, 1) or "summary" not in data:
                row.update(status="unverified", completion=data["completion"])
            else:
                summary = data["summary"]
                for field in ("model", "kernel", "candidate", "precision"):
                    if summary["target"][field] != entry[field]:
                        raise ValueError(f"Result target mismatch: {name}")
                if summary["manifest_sha256"] != sha(evidence_freeze / "manifest.json"):
                    raise ValueError(f"Result belongs to another freeze: {name}")
                for role in ("baseline", "repaired"):
                    p = str(Path(name).parent / f"{role}.py")
                    if sha(folder / f"{role}.py") != evidence_manifest["files"][p]:
                        raise ValueError(f"Evidence source changed: {p}")
                cases = summary["cases"]
                holdouts = [c for c in cases if c["holdout"]]
                control = [c for c in cases if not c["holdout"]]
                policy = read(evidence_freeze / "policy.json")
                if {
                    c["case"]["name"] if isinstance(c["case"], dict) else c["case"]
                    for c in holdouts
                } != {c["name"] for c in policy["cases"]}:
                    raise ValueError(f"Missing or extra holdout cases: {name}")
                if len(holdouts) != 12 or len(control) != 1:
                    raise ValueError(f"Incomplete case set: {name}")
                if control[0]["case"] != "canonical_control":
                    raise ValueError(f"Missing canonical control: {name}")
                passes = sum(c["passed"] for c in holdouts)
                if summary["holdout_passes"] != passes or summary["passed"] != all(
                    c["passed"] for c in cases
                ):
                    raise ValueError(f"Summary decision mismatch: {name}")
                finite = [
                    c["repaired_relative_l2"]
                    for c in holdouts
                    if c.get("repaired_relative_l2") is not None
                ]
                row.update(
                    status="completed",
                    canonical_pass=control[0]["passed"],
                    holdout_passes=passes,
                    holdout_cases=12,
                    full_holdout_pass=summary["passed"],
                    worst_finite_output_relative_l2=max(finite) if finite else None,
                    nonfinite_or_invalid_holdouts=12 - len(finite),
                )
                targets.append({"coverage": entry, "summary": summary})
        rows.append(row)
    totals = {
        "targets": len(rows),
        "completed_targets": sum(r["status"] == "completed" for r in rows),
        "pending_or_unverified_targets": sum(r["status"] != "completed" for r in rows),
        "full_holdout_passes": sum(r.get("full_holdout_pass", False) for r in rows),
        "canonical_passes": sum(r.get("canonical_pass", False) for r in rows),
        "individual_holdout_passes": sum(r.get("holdout_passes", 0) for r in rows),
        "individual_holdout_cases": sum(r.get("holdout_cases", 0) for r in rows),
    }
    report = {
        "scope": "Every full FP16 recovery in the frozen eligible primary paper inventory",
        "totals": totals,
        "rows": rows,
        "targets": targets,
        "coverage_manifest_sha256": sha(freeze / "manifest.json"),
        "policy": read(freeze / "policy.json"),
        "harness_sha256": manifest["harness_sha256"],
        "worst_finite_error_caveat": "Excludes invalid/nonfinite cases; these remain failures.",
    }
    write(output / "report.json", report)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    (output / "report.csv").write_text(stream.getvalue())
    print(json.dumps(totals, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--previous-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    collect(
        args.freeze.resolve(),
        args.results.resolve(),
        args.previous_results.resolve(),
        args.output.resolve(),
    )
