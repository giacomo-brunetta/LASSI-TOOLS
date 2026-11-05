from __future__ import annotations

import asyncio
import inspect
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from lassi_x.c_to_torch import TranslationPlan, _configs
from lassi_x.config import RunConfig
from lassi_x.execution import LocalExecutionBackend, put_bytes
from lassi_x.input_contract import load_contract, save_contract
from lassi_x.validation import build_oracle, validate_candidate
from lassi_x.workload_checks import (
    DEFAULT_SEEDS,
    RANDOM_FIELDS,
    configuration,
    prepare,
    random_inputs,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def prepared(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    if shutil.which("cc") is None:
        pytest.skip("C compiler unavailable")
    destination = tmp_path_factory.mktemp("workload-checks") / "prepared"
    return destination, asyncio.run(prepare(ROOT, destination, dataset="mini"))


@pytest.mark.parametrize("name", list(RANDOM_FIELDS))
def test_native_cases_execute_with_exact_inputs(
    prepared: tuple[Path, dict[str, Any]], name: str
) -> None:
    directory, report = prepared
    entry = next(w for w in report["workloads"] if w["id"] == "polybench/" + name)
    assert entry["status"] == "reference_checked", entry
    assert [c["id"] for c in entry["cases"]] == [f"random-{seed}" for seed in DEFAULT_SEEDS]
    config = RunConfig.model_validate(yaml.safe_load(Path(entry["config"]).read_text()))
    # Exercise the new pipeline's actual case loader, without invoking synthesis.
    plan = TranslationPlan.model_validate(
        {
            "cases": [c["path"] for c in entry["case_configs"]],
            "function": "main",
            "model": {"model": "not-called"},
            "native_python": sys.executable,
            "tenspiler_root": str(ROOT / "third_party/tenspiler"),
            "llvm_bin": str(ROOT),
            "llvm_pass": str(ROOT / "unused-in-loader-test.so"),
        }
    )
    loaded = _configs(plan)
    assert len(loaded) == len(DEFAULT_SEEDS)
    assert len({str(c.oracle.input_fixture) for c in loaded}) == len(DEFAULT_SEEDS)
    assert len(config.arena.correctness_tests) == 4
    original, _ = load_contract(directory / name / "native/oracle/c-fixture/inputs.npz")
    field = RANDOM_FIELDS[name]
    variants = []
    for seed in DEFAULT_SEEDS:
        alternate, _ = load_contract(directory / name / f"random-{seed}-inputs.npz")
        assert not np.array_equal(original[field], alternate[field])
        assert original[field].dtype == alternate[field].dtype
        assert original[field].shape == alternate[field].shape
        np.testing.assert_array_equal(alternate[field], random_inputs(name, original, seed)[field])
        for key in original.keys() - {field}:
            np.testing.assert_array_equal(original[key], alternate[key])
        variants.append(alternate[field])
    assert all(not np.array_equal(variants[0], other) for other in variants[1:])
    if name in {"cholesky", "lu"}:
        for value in variants:
            np.testing.assert_allclose(value, value.T)
            np.linalg.cholesky(value)


def test_unconfigured_native_dependencies_cannot_be_reported_as_checked(
    prepared: tuple[Path, dict[str, Any]],
) -> None:
    directory, report = prepared
    assert json.loads((directory / "report.json").read_text()) == report
    assert len(report["workloads"]) == 40
    unsupported = [w for w in report["workloads"] if w["status"] == "unsupported"]
    assert len(unsupported) == 10
    assert all(w["cases"] == [] for w in unsupported)


def test_rejects_changed_pinned_source(tmp_path: Path) -> None:
    source = tmp_path / "changed.c"
    source.write_text("int main(void) { return 0; }")
    with pytest.raises(ValueError, match="hash mismatch"):
        configuration(
            tmp_path,
            {"sources": [{"path": "changed.c", "sha256": "wrong"}]},
            tmp_path / "fixture.json",
            "mini",
        )


def test_real_pipeline_rejects_primary_only_candidate_and_rechecks_repair(
    prepared: tuple[Path, dict[str, Any]],
    tmp_path: Path,
) -> None:
    directory, _ = prepared
    config = RunConfig.model_validate(yaml.safe_load((directory / "gemm/run.yaml").read_text()))
    reference = asyncio.run(build_oracle(config, tmp_path / "reference"))
    backend = LocalExecutionBackend(tmp_path / "workspaces")
    workspace = "candidate"
    # Returning primary expected values demonstrates why a second value case matters.
    memorized = (
        "import torch\ndef forward(**kwargs):\n    return torch.tensor("
        + repr(reference.values.tolist())
        + ", dtype=torch.float64)\n"
    )
    asyncio.run(put_bytes(backend, workspace, "candidate.py", memorized.encode()))
    rejected = asyncio.run(
        validate_candidate(config, backend, workspace, reference, tmp_path / "bad")
    )
    assert not rejected.ok
    rows = json.loads((tmp_path / "bad/suite.json").read_text())
    assert rows[0]["status"] == "passed"
    assert rows[1]["status"] == "failed"
    corrected = (
        "def forward(ni, nj, nk, alpha, beta, A, B, C):\n    return alpha * (A @ B) + beta * C\n"
    )
    asyncio.run(put_bytes(backend, workspace, "candidate.py", corrected.encode()))
    accepted = asyncio.run(
        validate_candidate(config, backend, workspace, reference, tmp_path / "good")
    )
    assert accepted.ok, accepted.diagnostic
    rows = json.loads((tmp_path / "good/suite.json").read_text())
    assert [row["status"] for row in rows] == ["passed"] * len(DEFAULT_SEEDS)


def test_production_defaults_use_large_and_multiple_random_inputs() -> None:
    assert inspect.signature(prepare).parameters["dataset"].default == "large"
    manifest = json.loads((ROOT / "benchmarks/provenance/workloads-40.json").read_text())
    workload = next(w for w in manifest["workloads"] if w["id"] == "polybench/gemm")
    config = configuration(ROOT, workload, ROOT / "benchmarks/checks/gemm.json", "large")
    assert "-DLARGE_DATASET" in config.oracle.build
    assert config.kernel.validation_dataset == config.measure.evaluation_dataset == "large"
    assert len(DEFAULT_SEEDS) == 5


@pytest.mark.parametrize("seeds", [(1,), (1, 1), (-1, 2)])
def test_invalid_seed_suites_rejected(tmp_path: Path, seeds: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="distinct nonnegative"):
        asyncio.run(prepare(ROOT, tmp_path / "invalid", seeds=seeds))


def test_large_durbin_random_references(tmp_path: Path) -> None:
    """Exercise actual LARGE compilation/import and all five seeded references."""
    if shutil.which("cc") is None:
        pytest.skip("C compiler unavailable")
    manifest = json.loads((ROOT / "benchmarks/provenance/workloads-40.json").read_text())
    workload = next(w for w in manifest["workloads"] if w["id"] == "polybench/durbin")
    config = configuration(ROOT, workload, ROOT / "benchmarks/checks/durbin.json", "large")
    native = asyncio.run(build_oracle(config, tmp_path / "native"))
    assert native.input_contract_path is not None
    arrays, metadata = load_contract(native.input_contract_path)
    assert arrays["r"].shape == (2000,)
    outputs = []
    for seed in DEFAULT_SEEDS:
        inputs = tmp_path / f"random-{seed}.npz"
        save_contract(inputs, random_inputs("durbin", arrays, seed), metadata)
        case = config.validated_update(oracle=config.oracle.validated_update(input_fixture=inputs))
        oracle = asyncio.run(build_oracle(case, tmp_path / f"random-{seed}"))
        assert np.isfinite(oracle.values).all()
        outputs.append(oracle.values)
    assert all(not np.array_equal(outputs[0], other) for other in outputs[1:])
