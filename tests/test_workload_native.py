from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from lassi_x.c_to_torch import TranslationPlan, _configs, c_gate
from lassi_x.config import RunConfig
from lassi_x.input_contract import load_contract
from lassi_x.workload_checks import DEFAULT_SEEDS, prepare
from lassi_x.workload_inputs import FIELDS, random_inputs
from lassi_x.workload_invariants import check_native
from lassi_x.workload_native import KINDS

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def native_cases(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    dependencies = Path(
        os.environ.get("LASSI_WORKLOAD_NATIVE_ROOT", str(ROOT / "build/workload-native"))
    )
    provenance = dependencies / "dependencies.json"
    if not provenance.exists() or json.loads(provenance.read_text())["status"] != "complete":
        pytest.fail(
            "Build native dependencies first: python tools/prepare_workload_dependencies.py "
            "build/workload-native; or set LASSI_WORKLOAD_NATIVE_ROOT to the explicit prepared root"
        )
    directory = tmp_path_factory.mktemp("native-workloads") / "cases"
    report = asyncio.run(
        prepare(
            ROOT, directory, dataset="mini", native_root=dependencies, workload_ids=tuple(KINDS)
        )
    )
    return directory, report


def row_for(report: dict[str, Any], workload_id: str) -> dict[str, Any]:
    return next(w for w in report["workloads"] if w["id"] == workload_id)


@pytest.mark.parametrize("workload_id", list(KINDS))
def test_five_native_random_cases_and_independent_checks(
    native_cases: tuple[Path, dict[str, Any]],
    workload_id: str,
) -> None:
    directory, report = native_cases
    row = row_for(report, workload_id)
    assert row["status"] == "reference_checked", row
    assert [c["seed"] for c in row["cases"]] == list(DEFAULT_SEEDS)
    # Exercise the new pipeline's actual case loader, without invoking synthesis.
    plan = TranslationPlan.model_validate(
        {
            "cases": [c["path"] for c in row["case_configs"]],
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
    assert len({c["output_sha256"] for c in row["cases"]}) == len(DEFAULT_SEEDS)
    name, kind = workload_id.split("/")[-1], KINDS[workload_id]
    baseline, _ = load_contract(directory / name / "native/oracle/c-fixture/inputs.npz")
    for case in row["cases"]:
        inputs, _ = load_contract(directory / name / (case["id"] + "-inputs.npz"))
        outputs, _ = load_contract(directory / name / case["id"] / "oracle/c-fixture/outputs.npz")
        metrics = check_native(kind, inputs, outputs)
        assert metrics == case["independent_checks"]
        regenerated = random_inputs(kind, baseline, case["seed"])
        for field in FIELDS[kind]:
            np.testing.assert_array_equal(inputs[field], regenerated[field])
            assert inputs[field].shape == baseline[field].shape
            assert inputs[field].dtype == baseline[field].dtype
        # Independent equations/invariants must reject a finite, shape-correct wrong result.
        corrupted = {name: np.zeros_like(value) for name, value in outputs.items()}
        with pytest.raises(ValueError, match="independent check failed"):
            check_native(kind, inputs, corrupted)


@pytest.mark.parametrize("workload_id", list(KINDS))
def test_native_c_preflight_checks_every_case(
    native_cases: tuple[Path, dict[str, Any]],
    workload_id: str,
    tmp_path: Path,
) -> None:
    _, report = native_cases
    row = row_for(report, workload_id)
    assert row["status"] == "reference_checked", row
    config = RunConfig.model_validate(yaml.safe_load(Path(row["config"]).read_text()))
    cases = [config] + [
        config.validated_update(oracle=c.oracle) for c in config.arena.correctness_tests
    ]
    assert len(cases) == len(DEFAULT_SEEDS)
    for case, seed in zip(cases, DEFAULT_SEEDS, strict=True):
        gate = asyncio.run(
            c_gate(
                case,
                config.resolve_project_path(config.kernel.reference),
                tmp_path / f"seed-{seed}",
            )
        )
        assert gate["passed"], gate
        assert any(check["read_only"] for check in gate["checks"])
        assert all(check["expected_sha256"] == check["observed_sha256"] for check in gate["checks"])


@pytest.mark.parametrize("workload_id", list(KINDS))
def test_native_c_gate_rejects_erased_outputs(
    native_cases: tuple[Path, dict[str, Any]],
    workload_id: str,
    tmp_path: Path,
) -> None:
    _, report = native_cases
    row = row_for(report, workload_id)
    assert row["status"] == "reference_checked", row
    config = RunConfig.model_validate(yaml.safe_load(Path(row["config"]).read_text()))
    assert config.oracle.fixture_spec is not None
    spec = json.loads(config.resolve_project_path(config.oracle.fixture_spec).read_text())
    output = spec["outputs"][0]
    field = spec["fields"][output]
    element = f"({field['expression']})" + "[0]" * len(field["shape"])
    count = " * ".join(f"(size_t)({n})" for n in field["shape"]) or "1"
    source = config.resolve_project_path(config.kernel.reference).read_text()
    source = "#include <string.h>\n" + source.replace(
        "/* LASSI_END */",
        f"memset(&({element}), 0, sizeof({element}) * ({count}));\n/* LASSI_END */",
    )
    candidate = tmp_path / "erased.c"
    candidate.write_text(source)
    gate = asyncio.run(c_gate(config, candidate, tmp_path / "gate"))
    assert not gate["passed"]
    assert any(not check["passed"] for check in gate["checks"] if not check["read_only"])
