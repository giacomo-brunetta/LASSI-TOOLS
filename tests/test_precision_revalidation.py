from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from lassi_x.precision_revalidation import plan_revalidation

from .test_precision_integrity import point


def test_plan_keeps_raw_results_and_never_requires_models(tmp_path: Path) -> None:
    record_path = tmp_path / "run.json"
    observation = point().to_dict()
    record_path.write_text(
        json.dumps({"measurements": [observation, observation], "config_path": "config.yaml"})
    )
    original = record_path.read_bytes()
    result = plan_revalidation(tmp_path)
    assert record_path.read_bytes() == original
    assert result["raw_results_modified"] is False
    assert result["model_calls_required"] == 0
    assert len(result["targets"]) == 1
    assert len(result["targets"][0]["original_observations"]) == 2


def clean_runner() -> Any:
    path = (
        Path(__file__).resolve().parents[1] / "examples/cpu-ablation-suite/run_clean_gpu_repairs.py"
    )
    spec = importlib.util.spec_from_file_location("clean_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reuses_fp64_but_not_uncertified_fp32_controls() -> None:
    cell = {"sha256": "source"}
    high = point().to_dict()
    high.update(
        precision="fp64",
        source_hash="source",
        source_integrity_verified=True,
        evaluation_dataset="large",
    )
    middle = {**high, "precision": "fp32"}
    old = {"cell": cell, "measurements": [high, middle]}
    runner = clean_runner()
    assert set(runner.cached_controls(old, cell)) == {"fp64"}
    assert not runner.cached_controls(old, {"sha256": "changed"})


def test_precision_failure_is_not_a_numerical_repair_target() -> None:
    runner = clean_runner()
    high = point().to_dict()
    high.update(precision="fp64", notes="")
    low = point().to_dict()
    low.update(precision_verdict="failed", failure_kind="precision_policy")
    assert runner.classification([high, low], {}) == "invalid_precision_promotion"
    low.update(precision_verdict="unverified", failure_kind="")
    assert runner.classification([high, low], {}) == "precision_unverified"
