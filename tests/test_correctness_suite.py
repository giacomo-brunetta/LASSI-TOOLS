from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from lassi_x.config import CorrectnessTestConfig
from lassi_x.input_contract import save_contract
from lassi_x.types import Diagnostic
from lassi_x.validation import OracleResult, ValidationResult, build_oracle, validate_candidate

from .test_validation import _setup

if TYPE_CHECKING:
    from pathlib import Path


def suite(tmp_path: Path) -> Any:
    config, backend = _setup(tmp_path)
    config.arena.correctness_tests = [
        CorrectnessTestConfig(
            id=name, dataset=name, oracle=config.oracle, input_contract=tmp_path / "inputs.npz"
        )
        for name in ("edge", "large")
    ]
    oracle = OracleResult(tmp_path / "oracle.npy", np.array([1.0]))
    return config, backend, oracle


def test_suite_reports_each_case_and_rechecks_after_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, oracle = suite(tmp_path)
    calls = []
    failing = True

    async def reference(*args: Any) -> Any:
        return oracle

    async def check(cfg: Any, *args: Any, **kwargs: Any) -> Any:
        name = cfg.kernel.validation_dataset
        calls.append(name)
        ok = not (failing and name == "edge")
        return ValidationResult(ok, None if ok else Diagnostic("equivalence", "wrong values"), None)

    monkeypatch.setattr("lassi_x.validation.build_oracle", reference)
    monkeypatch.setattr("lassi_x.validation._validate_single_candidate", check)
    for attempt in range(2):
        result = asyncio.run(
            validate_candidate(config, backend, "good", oracle, tmp_path / str(attempt))
        )
        assert result.ok == (attempt == 1)
        if attempt == 0:
            assert result.diagnostic is not None
            assert "edge (dataset=edge): failed" in result.diagnostic.message
            assert "large (dataset=large): passed" in result.diagnostic.message
        failing = False
    assert calls == [config.kernel.validation_dataset, "edge", "large"] * 2


def test_suite_reports_unexecuted_cases_after_compile_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, oracle = suite(tmp_path)

    async def check(*args: Any, **kwargs: Any) -> Any:
        return ValidationResult(False, Diagnostic("compile", "invalid syntax"), None)

    monkeypatch.setattr("lassi_x.validation._validate_single_candidate", check)
    result = asyncio.run(validate_candidate(config, backend, "good", oracle, tmp_path / "report"))
    rows = json.loads((tmp_path / "report/suite.json").read_text())
    assert [row["status"] for row in rows] == ["failed", "not_run", "not_run"]
    assert result.diagnostic is not None
    assert "edge (dataset=edge): not_run" in result.diagnostic.message
    assert not result.ok


def test_reference_failure_is_inconclusive_and_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, oracle = suite(tmp_path)

    async def check(*args: Any, **kwargs: Any) -> Any:
        return ValidationResult(True, None, None)

    async def reference(*args: Any) -> Any:
        raise RuntimeError("reference unavailable")

    monkeypatch.setattr("lassi_x.validation._validate_single_candidate", check)
    monkeypatch.setattr("lassi_x.validation.build_oracle", reference)
    with pytest.raises(RuntimeError, match="reference unavailable"):
        asyncio.run(validate_candidate(config, backend, "good", oracle, tmp_path / "report"))
    rows = json.loads((tmp_path / "report/suite.json").read_text())
    assert [row["status"] for row in rows] == ["passed", "inconclusive", "not_run"]


def test_duplicate_and_reserved_ids_rejected(tmp_path: Path) -> None:
    config, _, _ = suite(tmp_path)
    for ids in (["edge", "edge"], ["primary", "edge"]):
        tests = [
            test.model_copy(update={"id": name})
            for test, name in zip(config.arena.correctness_tests, ids, strict=True)
        ]
        with pytest.raises(ValueError, match="unique"):
            type(config.arena).model_validate(
                {**config.arena.model_dump(), "correctness_tests": tests}
            )


def test_real_suite_checks_reference_and_trusted_inputs(tmp_path: Path) -> None:
    config, backend = _setup(tmp_path)
    contract = tmp_path / "inputs.npz"
    save_contract(
        contract,
        {"x": np.array([1.0, 2.0, 3.0])},
        {"kernel": "tiny", "dataset": "edge", "required": ["x"]},
    )
    config.arena.correctness_tests = [
        CorrectnessTestConfig(
            id="edge", dataset="edge", oracle=config.oracle, input_contract=contract
        )
    ]
    oracle = asyncio.run(build_oracle(config, tmp_path / "reference"))
    result = asyncio.run(validate_candidate(config, backend, "good", oracle, tmp_path / "pass"))
    assert result.ok
    save_contract(
        contract,
        {"x": np.array([9.0, 2.0, 3.0])},
        {"kernel": "tiny", "dataset": "edge", "required": ["x"]},
    )
    result = asyncio.run(validate_candidate(config, backend, "good", oracle, tmp_path / "fail"))
    assert not result.ok
    rows = json.loads((tmp_path / "fail/suite.json").read_text())
    assert [row["status"] for row in rows] == ["passed", "failed"]
    assert rows[1]["diagnostic"]["gate"] == "inputs"


def test_budget_exhaustion_keeps_passes_and_lists_unexecuted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, oracle = suite(tmp_path)
    elapsed = [0.0]
    config.arena.suite_timeout_s = 1

    async def check(*args: Any, **kwargs: Any) -> Any:
        elapsed[0] = 2.0
        return ValidationResult(True, None, None)

    monkeypatch.setattr("lassi_x.validation.time.monotonic", lambda: elapsed[0])
    monkeypatch.setattr("lassi_x.validation._validate_single_candidate", check)
    result = asyncio.run(validate_candidate(config, backend, "good", oracle, tmp_path / "budget"))
    assert not result.ok
    rows = json.loads((tmp_path / "budget/suite.json").read_text())
    assert [row["status"] for row in rows] == ["passed", "not_run", "not_run"]
    assert all("budget exhausted" in row["reason"] for row in rows[1:])
