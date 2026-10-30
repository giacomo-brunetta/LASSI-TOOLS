"""Coverage reporting must retain numerical failures and reject missing evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from lassi_x.holdout import sha, write

SCRIPT = (
    Path(__file__).resolve().parents[1] / "experiments/holdout-validation/report_fp16_holdout.py"
)
spec = importlib.util.spec_from_file_location("fp16_holdout_report", SCRIPT)
assert spec and spec.loader
reporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporter)


@pytest.fixture
def evidence(tmp_path):
    freeze, results, old = [tmp_path / n for n in ("freeze", "results", "old")]
    relative = "luna/poisson-cg/c1-fp16"
    for role in ("baseline", "repaired"):
        source = freeze / relative / f"{role}.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"# frozen {role}\n")
    write(freeze / "policy.json", {"cases": [{"name": f"case_{i}"} for i in range(12)]})
    write(
        freeze / "coverage.json",
        [
            {
                "model": "luna",
                "kernel": "poisson-cg",
                "candidate": "c1",
                "precision": "fp16",
                "selection": "retained_source_bound_remeasurement",
                "target": relative + "/target.json",
                "disposition": "new_evaluation",
                "source_sha256": sha(freeze / relative / "repaired.py"),
            }
        ],
    )
    write(
        freeze / "manifest.json",
        {
            "harness_sha256": {},
            "files": {str(p.relative_to(freeze)): sha(p) for p in freeze.rglob("*") if p.is_file()},
        },
    )
    cases = [{"case": "canonical_control", "holdout": False, "passed": True}]
    cases += [
        {
            "case": f"case_{i}",
            "holdout": True,
            "passed": i != 3,
            "repaired_relative_l2": 0.02 if i == 3 else 0.001,
        }
        for i in range(12)
    ]
    write(
        results / "results.json",
        {
            relative + "/target.json": {
                "completion": {"returncode": 1},
                "summary": {
                    "target": {
                        "model": "luna",
                        "kernel": "poisson-cg",
                        "candidate": "c1",
                        "precision": "fp16",
                    },
                    "manifest_sha256": sha(freeze / "manifest.json"),
                    "cases": cases,
                    "holdout_passes": 11,
                    "passed": False,
                },
            }
        },
    )
    write(old / "results.json", {})
    return freeze, results, old, tmp_path / "report"


def test_numerical_failure_is_a_completed_result(evidence):
    report = reporter.collect(*evidence)
    assert report["totals"]["completed_targets"] == 1
    assert report["totals"]["full_holdout_passes"] == 0
    assert report["totals"]["individual_holdout_passes"] == 11
    assert report["rows"][0]["status"] == "completed"


def test_missing_case_cannot_be_reported_as_complete(evidence):
    path = evidence[1] / "results.json"
    data = json.loads(path.read_text())
    next(iter(data.values()))["summary"]["cases"].pop()
    write(path, data)
    with pytest.raises(ValueError, match="Missing or extra holdout"):
        reporter.collect(*evidence)


def test_source_drift_cannot_reuse_a_result(evidence):
    (evidence[0] / "luna/poisson-cg/c1-fp16/repaired.py").write_text("# changed\n")
    with pytest.raises(ValueError, match="Freeze changed"):
        reporter.collect(*evidence)
