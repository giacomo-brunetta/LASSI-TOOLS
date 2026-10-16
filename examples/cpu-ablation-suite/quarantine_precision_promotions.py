"""Retire confirmed promotion cells only, preserving originals and valid FP64 work."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

from lassi_x.artifacts import atomic_write, write_json
from lassi_x.types import Diagnostic

REPO = Path(__file__).resolve().parents[2]
ARCHIVE = REPO / "runs/legacy/precision-policy-20261016/confirmed-promotions"
REVIEW = REPO / "runs/a100-clean-gpu-repairs-20261016/saved-campaign-runtime-policy-audit.json"
OLD_DERICHE = REPO / "runs/a100-terra-medium-20261010/runs/polybench-deriche"
MOVED_DERICHE = REPO / "runs/legacy/precision-policy-20261016/terra-deriche/mini-runs"


def actual_path(path: str) -> Path:
    source = Path(path)
    if not source.exists() and source.is_relative_to(OLD_DERICHE):
        source = MOVED_DERICHE / source.relative_to(OLD_DERICHE)
    return source


def cases() -> list[dict]:
    result = []
    for r in json.loads(REVIEW.read_text())["records"]:
        if r["status"] != "violation":
            continue
        # Jacobi is a constant/scalar normalization issue, not a promoted kernel.
        if r["kernel"].startswith("polybench-jacobi-2d"):
            continue
        result.append(
            {
                "model": "terra" if "terra-medium" in r["campaign"] else "luna",
                "kernel": r["kernel"].removesuffix("-mini"),
                "candidate": r["candidate"],
                "precision": r["precision"],
                "module": r["module"],
                "reason": "Confirmed wider computation or wrong-format supplied input",
                "evidence": r["audit"],
                "original_campaign": r["campaign"],
            }
        )
    oss = REPO / "runs/cpu-gpt-oss-120b-openrouter-groq-medium-20261015"
    for r in json.loads((oss / "precision-policy-review-20261016.json").read_text())["records"]:
        if (r["kernel"], r["candidate"]) not in {
            ("polybench-correlation", "c3"),
            ("polybench-adi", "c3"),
            ("direct-dft", "c2"),
            ("direct-dft", "c3"),
        }:
            continue
        result.append(
            {
                "model": "oss",
                **r,
                "reason": "Explicit whole-data FP64 promotion; invalid for this requested format",
                "fp64_translation_validity": "unchanged",
                "original_campaign": oss.name,
            }
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    selected = cases()
    if not args.apply:
        print(
            json.dumps({"cases": len(selected), "models": sorted({c["model"] for c in selected})})
        )
        return 0
    if ARCHIVE.exists():
        raise FileExistsError("Quarantine already exists; refusing a second mutation")
    ARCHIVE.mkdir(parents=True)
    by_run: dict[Path, list[dict]] = {}
    manifest = []
    for index, cell in enumerate(selected, 1):
        source = actual_path(cell["module"])
        if not source.is_file():
            raise FileNotFoundError(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if cell.get("source_hash") and digest != cell["source_hash"]:
            raise ValueError(f"Audited source changed: {source}")
        dest = ARCHIVE / cell["model"] / cell["kernel"] / f"{cell['candidate']}-{cell['precision']}"
        dest.mkdir(parents=True)
        shutil.copy2(source, dest / "candidate.py")
        write_json(
            dest / "INVALID_RESULTS.json",
            {
                **cell,
                "valid_results": False,
                "publishable": False,
                "resume_allowed": False,
                "source_sha256": digest,
                "actual_source_location": str(source),
                "scope": f"Requested {cell['precision']} only; valid FP64 CPU evidence is retained",
            },
        )
        run = next(p for p in source.parents if (p / "run.json").is_file())
        by_run.setdefault(run, []).append(cell)
        manifest.append(
            {
                "id": index,
                "model": cell["model"],
                "kernel": cell["kernel"],
                "candidate": cell["candidate"],
                "precision": cell["precision"],
                "module": cell["module"],
                "source_sha256": digest,
                "invalid_record": str(dest / "INVALID_RESULTS.json"),
            }
        )

    measurements_changed = 0
    for index, (run, cells_for_run) in enumerate(by_run.items(), 1):
        snapshot = ARCHIVE / "original-records" / str(index)
        snapshot.mkdir(parents=True)
        lookup = {(c["module"], c["precision"]): c for c in cells_for_run}

        def invalidate(point: dict, lookup: dict = lookup) -> dict:
            nonlocal measurements_changed
            if (point.get("module_path"), point.get("precision")) not in lookup:
                return point
            result = copy.deepcopy(point)
            result.update(
                status="rejected",
                precision_verdict="failed",
                failure_kind="precision_policy",
                frontier_eligible=False,
                precision_eligible=False,
                stable_success=False,
            )
            result["notes"] = (
                result.get("notes", "")
                + "; INVALID: confirmed precision promotion; "
                + str(ARCHIVE / "INVALID_RESULTS.json")
            ).strip("; ")
            measurements_changed += 1
            return result

        # Snapshots and trace directories remain recoverable. Do not rewrite the
        # already-quarantined Deriche evidence a second time.
        for name in (
            "run.json",
            "measurements.jsonl",
            "frontier.json",
            "checkpoint.json",
            "summary.md",
        ):
            path = run / name
            if path.exists():
                shutil.copy2(path, snapshot / name)
        write_json(snapshot / "original-location.json", {"run_dir": str(run)})
        if run.is_relative_to(MOVED_DERICHE):
            continue
        path = run / "run.json"
        record = json.loads(path.read_text())
        record["measurements"] = [invalidate(p) for p in record.get("measurements", [])]
        record["frontier"] = [
            p
            for p in record.get("frontier", [])
            if (p.get("module_path"), p.get("precision")) not in lookup
        ]
        for candidate in record.get("compatibility_candidates", []):
            if (candidate.get("module_path"), candidate.get("target_precision")) in lookup:
                candidate["status"] = "rejected"
                candidate.setdefault("diagnostics", []).append(
                    Diagnostic(
                        gate="precision-policy",
                        message="Invalidated confirmed promotion; source archived",
                    ).to_dict()
                )
        record.setdefault("evaluation", {})["precision_invalidation"] = {
            "manifest": str(ARCHIVE / "INVALID_RESULTS.json"),
            "cells": [
                {k: c[k] for k in ("candidate", "precision", "module")} for c in cells_for_run
            ],
            "cpu_fp64_translation_validity": "unchanged",
        }
        if record.get("status") in {"ok", "partial"}:
            record["status"] = "partial"
            record.setdefault("acceptance", {})["passed"] = False
        write_json(path, record)
        # New readers must not see an old successful counterpart in JSONL/frontier.
        jsonl = run / "measurements.jsonl"
        if jsonl.exists():
            rows = [
                invalidate(json.loads(line))
                for line in jsonl.read_text().splitlines()
                if line.strip()
            ]
            atomic_write(jsonl, "".join(json.dumps(p) + "\n" for p in rows))
        if (run / "frontier.json").exists():
            write_json(run / "frontier.json", record["frontier"])
        # Prevent an old completed checkpoint from resurrecting retired results.
        write_json(
            run / "INVALID_PRECISION_CELLS.json",
            {
                "manifest": str(ARCHIVE / "INVALID_RESULTS.json"),
                "scope": "Listed cells only; other candidates and FP64 remain usable",
                "cells": record["evaluation"]["precision_invalidation"]["cells"],
                "old_checkpoint_resume_allowed": False,
            },
        )
        summary = run / "summary.md"
        if summary.exists():
            atomic_write(
                summary,
                "> Precision promotion cases invalidated; see INVALID_PRECISION_CELLS.json.\n\n"
                + summary.read_text(),
            )
    write_json(
        ARCHIVE / "INVALID_RESULTS.json",
        {
            "status": "confirmed_precision_promotions",
            "valid_results": False,
            "publishable": False,
            "resume_allowed": False,
            "cases": manifest,
            "source_precision_cases": len(manifest),
            "note": (
                "Counts include exploratory OSS format probes, not additional historical GPU runs. "
                "Constant-only and host-scalar flags are excluded. CPU FP64 results remain intact."
            ),
        },
    )
    print(
        json.dumps(
            {
                "archived_cases": len(manifest),
                "originals_preserved": True,
                "measurement_rows_updated_including_jsonl": measurements_changed,
                "archive": str(ARCHIVE),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
