#!/usr/bin/env python3
"""Aggregate candidate-accuracy metrics from a paper-suite journal."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _arguments() -> argparse.Namespace:
    """Parse the journal path.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("journal", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def summarize(journal: Path) -> dict[str, Any]:
    """Aggregate final run artifacts referenced by a session journal.

    Args:
        journal: JSONL session journal produced by ``run_suite.py``.

    Returns:
        Model-level candidate and kernel accuracy totals.
    """
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing: list[str] = []
    for line in journal.read_text().splitlines():
        event = json.loads(line)
        if event.get("event") != "finish" or event.get("exit_code") != 0:
            continue
        run_dir = event.get("run_dir")
        run_path = Path(run_dir) / "run.json" if run_dir else None
        if run_path is None or not run_path.is_file():
            missing.append(f"{event.get('model')}:{event.get('kernel')}")
            continue
        groups[str(event["model"])].append(json.loads(run_path.read_text()))
    models: dict[str, Any] = {}
    for model, runs in groups.items():
        samples = sum(int(run["accuracy"]["samples"]) for run in runs)
        initial = sum(int(run["accuracy"]["initial_passes"]) for run in runs)
        final = sum(int(run["accuracy"]["final_passes"]) for run in runs)
        recovered = sum(int(run["accuracy"]["recovered_by_repair"]) for run in runs)
        solved = sum(bool(run["accuracy"]["kernel_solved"]) for run in runs)
        models[model] = {
            "runs": len(runs),
            "candidate_samples": samples,
            "initial_passes": initial,
            "final_passes": final,
            "recovered_by_repair": recovered,
            "initial_candidate_pass_rate": initial / samples if samples else 0.0,
            "final_candidate_pass_rate": final / samples if samples else 0.0,
            "kernel_solve_rate": solved / len(runs) if runs else 0.0,
        }
    return {
        "schema_version": 1,
        "journal": str(journal.resolve()),
        "models": models,
        "missing_run_artifacts": missing,
        "sampling_note": (
            "Candidate rates aggregate strategy-diverse arena attempts. Canonical pass@k "
            "requires IID generations with a fixed prompt and decoding policy."
        ),
    }


def main() -> int:
    """Write and print the suite accuracy summary.

    Returns:
        Zero after successful aggregation.
    """
    args = _arguments()
    result = summarize(args.journal)
    output = args.output or args.journal.with_suffix(".summary.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
