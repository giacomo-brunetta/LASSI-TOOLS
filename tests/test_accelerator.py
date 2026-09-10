from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import numpy as np

import lassi_x.accelerator as accelerator
from lassi_x.accelerator import (
    compatibility_accuracy_diagnostic,
    repair_accelerator_candidate,
    select_compatibility_failures,
)
from lassi_x.config import RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.hermes import HermesTurn
from lassi_x.measurement import Backend
from lassi_x.types import Candidate, Measurement, Status, Usage
from lassi_x.validation import OracleResult, ValidationResult

from .test_config import minimal_config

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lassi_x.config import BackendConfig


def _point(backend: str, precision: str, status: Status) -> Measurement:
    return Measurement(
        kernel="tiny",
        candidate_id="c1",
        variant_id="c1-base",
        backend=backend,
        precision=precision,
        compensation="none",
        status=status,
        module_path="candidate.py",
        storage_precision=precision,
        operator_precision=precision,
        accumulator_precision=precision,
        output_precision=precision,
        evaluation_output_checked=status == Status.OK,
        evaluation_output_finite=True if status == Status.OK else None,
        evaluation_semantic_verified=status == Status.OK,
        accuracy_source="timed_device_workload" if status == Status.OK else "",
    )


def test_compatibility_failures_are_accelerator_only_and_cell_deduplicated(
    tmp_path: Path,
) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda",
            "precisions": ["fp32", "fp16"],
        }
    )
    config = RunConfig.model_validate(data)
    selected = select_compatibility_failures(
        config,
        [
            _point("cpu", "fp32", Status.CRASHED),
            _point("cuda", "fp16", Status.CRASHED),
            _point("cuda", "fp32", Status.CRASHED),
            _point("cuda", "bf16", Status.UNSUPPORTED),
        ],
    )
    assert [(point.backend, point.precision) for point in selected] == [
        ("cuda", "fp32"),
        ("cuda", "fp16"),
    ]


def test_base_and_portable_numerical_sources_get_independent_platform_leaves(
    tmp_path: Path,
) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda",
            "precisions": ["fp16"],
        }
    )
    config = RunConfig.model_validate(data)
    base = _point("cuda", "fp16", Status.CRASHED)
    numerical = _point("cuda", "fp16", Status.CRASHED)
    numerical.variant_id = "n-c1-fp16"
    numerical.compensation = "kahan"
    selected = select_compatibility_failures(config, [base, numerical])
    assert [point.variant_id for point in selected] == ["c1-base", "n-c1-fp16"]


def test_compatibility_accuracy_gate_rejects_parent_regression(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    parent = _point("cpu", "fp16", Status.OK)
    parent.max_rel_error = 0.01
    patched = _point("cpu", "fp16", Status.OK)
    patched.max_rel_error = 0.02
    diagnostic = compatibility_accuracy_diagnostic(config, parent, patched)
    assert diagnostic is not None
    assert diagnostic.gate == "compatibility-accuracy"
    assert "regressed" in diagnostic.message


def test_newly_executable_compatibility_leaf_must_meet_threshold(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    parent = _point("cpu", "fp16", Status.CRASHED)
    patched = _point("cpu", "fp16", Status.OK)
    patched.max_rel_error = 0.02
    diagnostic = compatibility_accuracy_diagnostic(config, parent, patched)
    assert diagnostic is not None
    assert "exceeds the acceptance threshold" in diagnostic.message


class CompatibilitySession:
    def __init__(self, *_: object, **kwargs: Any) -> None:
        self.cwd = kwargs["cwd"]
        self.turn = 0

    async def send(self, _: str) -> HermesTurn:
        self.turn += 1
        target = self.cwd / "candidate.py"
        target.write_text(target.read_text() + f"\nCOMPAT_TURN = {self.turn}\n")
        return HermesTurn("edited", Usage())

    async def close(self) -> None:
        return None


class EventuallyCompatibleBackend(Backend[Any]):
    def __init__(self, spec: BackendConfig) -> None:
        super().__init__(spec)
        self.calls = 0

    async def measure(
        self,
        config: RunConfig,
        oracle: OracleResult,
        module_path: Path,
        *,
        candidate_id: str,
        variant_id: str,
        precision: str,
        compensation: str,
        seed: int = 0,
    ) -> Measurement:
        del config, oracle, module_path, seed
        self.calls += 1
        return Measurement(
            kernel="tiny",
            candidate_id=candidate_id,
            variant_id=variant_id,
            backend=self.spec.name,
            precision=precision,
            compensation=compensation,
            status=Status.CRASHED if self.calls == 1 else Status.OK,
            module_path="candidate.py",
            storage_precision=precision,
            operator_precision=precision,
            accumulator_precision=precision,
            output_precision=precision,
            latency_s=None if self.calls == 1 else 1.0,
            max_rel_error=None if self.calls == 1 else 0.1,
            evaluation_output_checked=self.calls != 1,
            evaluation_output_finite=True if self.calls != 1 else None,
            evaluation_semantic_verified=self.calls != 1,
            accuracy_source="timed_device_workload" if self.calls != 1 else "",
            notes="compile rejected" if self.calls == 1 else "",
        )


class DivergedBackend(Backend[Any]):
    async def measure(
        self,
        config: RunConfig,
        oracle: OracleResult,
        module_path: Path,
        *,
        candidate_id: str,
        variant_id: str,
        precision: str,
        compensation: str,
        seed: int = 0,
    ) -> Measurement:
        del config, oracle, module_path, seed
        return Measurement(
            kernel="tiny",
            candidate_id=candidate_id,
            variant_id=variant_id,
            backend=self.spec.name,
            precision=precision,
            compensation=compensation,
            status=Status.DIVERGED,
            module_path="candidate.py",
            storage_precision=precision,
            operator_precision=precision,
            accumulator_precision=precision,
            output_precision=precision,
            latency_s=1.0,
            max_rel_error=0.1,
            notes="strict precision mismatch",
        )


def test_compatibility_repair_receives_real_target_feedback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = minimal_config(tmp_path)
    data["compatibility"] = {"correction_rounds": 1}
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda",
            "precisions": ["fp32"],
        }
    )
    (tmp_path / "tiny.c").write_text("int main(void) { return 0; }")
    config = RunConfig.model_validate(data)
    base_path = tmp_path / "base.py"
    base_path.write_text("def make_model():\n    return None\n")
    base = Candidate("c1", "model", None, "direct", base_path, status=Status.OK)
    failure = _point("cuda", "fp32", Status.CRASHED)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0]))
    oracle = OracleResult(oracle_path, np.asarray([1.0]))

    async def accepted(*_: object, **__: object) -> ValidationResult:
        return ValidationResult(True, None, np.asarray([1.0]))

    monkeypatch.setattr(accelerator, "HermesSession", CompatibilitySession)
    monkeypatch.setattr(accelerator, "validate_candidate", accepted)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    async def run() -> tuple[Candidate, Measurement | None]:
        async with await ExecutionContext.start(
            config, run_dir, hermes_home=tmp_path / "hermes"
        ) as execution:
            return await repair_accelerator_candidate(
                config,
                oracle,
                run_dir,
                execution,
                base,
                failure,
                EventuallyCompatibleBackend(config.measure.backends[1]),
            )

    repaired, measurement = asyncio.run(run())
    assert repaired.status == Status.OK
    assert repaired.correction_rounds == 1
    assert measurement is not None and measurement.status == Status.OK


def test_strict_precision_divergence_does_not_pass_compatibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = minimal_config(tmp_path)
    data["compatibility"] = {"correction_rounds": 0}
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda",
            "precisions": ["fp32"],
        }
    )
    (tmp_path / "tiny.c").write_text("int main(void) { return 0; }")
    config = RunConfig.model_validate(data)
    base_path = tmp_path / "base.py"
    base_path.write_text("def make_model():\n    return None\n")
    base = Candidate("c1", "model", None, "direct", base_path, status=Status.OK)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0]))
    oracle = OracleResult(oracle_path, np.asarray([1.0]))

    async def accepted(*_: object, **__: object) -> ValidationResult:
        return ValidationResult(True, None, np.asarray([1.0]))

    monkeypatch.setattr(accelerator, "HermesSession", CompatibilitySession)
    monkeypatch.setattr(accelerator, "validate_candidate", accepted)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    async def run() -> tuple[Candidate, Measurement | None]:
        async with await ExecutionContext.start(
            config, run_dir, hermes_home=tmp_path / "hermes"
        ) as execution:
            return await repair_accelerator_candidate(
                config,
                oracle,
                run_dir,
                execution,
                base,
                _point("cuda", "fp32", Status.CRASHED),
                DivergedBackend(config.measure.backends[1]),
            )

    repaired, measurement = asyncio.run(run())
    assert repaired.status == Status.REJECTED
    assert measurement is not None and measurement.status == Status.DIVERGED
