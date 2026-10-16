from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import yaml

import lassi_x.compensation as compensation
from lassi_x.config import RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.hermes import HermesTurn
from lassi_x.measurement import Backend
from lassi_x.types import Candidate, Measurement, Status, Usage
from lassi_x.validation import OracleResult, ValidationResult

from .test_config import minimal_config
from .test_validation import GOOD_MODULE

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lassi_x.config import BackendConfig


def test_compensation_prompt_bounds_tensor_and_tool_output() -> None:
    assert "Bounded tool output (hard requirement)" in compensation.COMPENSATION_SYSTEM
    assert "bounded-tool-output-v1" in compensation.COMPENSATION_SYSTEM
    assert "tensors or numerical" in compensation.COMPENSATION_SYSTEM


def point(
    candidate_id: str,
    *,
    error: float,
    latency: float = 1.0,
    status: Status = Status.OK,
) -> Measurement:
    return Measurement(
        kernel="tiny",
        candidate_id=candidate_id,
        variant_id=f"{candidate_id}-base",
        backend="cpu",
        precision="fp16",
        compensation="none",
        status=status,
        module_path="candidate.py",
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        source_hash="fixture-source",
        precision_verdict="passed",
        precision_audit_protocol="executed-dtype-v3",
        precision_audit_source_hash="fixture-source",
        latency_s=latency,
        max_rel_error=error,
        relative_l2=error,
    )


def test_single_survivor_above_absolute_threshold_is_selected() -> None:
    weak = point("c1", error=0.4)
    assert compensation.select_weak_points([weak], error_threshold=0.1) == [weak]


def test_cross_candidate_domination_is_opt_in() -> None:
    leader = point("c1", error=0.01, latency=0.5)
    loser = point("c2", error=0.02, latency=1.0)
    assert compensation.select_weak_points([leader, loser], error_threshold=None) == []
    assert compensation.select_weak_points(
        [leader, loser], error_threshold=None, comparison_scope="cross_candidate"
    ) == [loser]


def test_domination_uses_the_configured_error_metric() -> None:
    leader = point("c1", error=0.5, latency=0.5)
    loser = point("c2", error=0.1, latency=1.0)
    leader.relative_l2 = 0.01
    loser.relative_l2 = 0.02
    assert compensation.select_weak_points(
        [leader, loser],
        error_threshold=None,
        error_metric="relative_l2",
        comparison_scope="cross_candidate",
    ) == [loser]


def test_missing_configured_error_metric_is_not_silently_accepted() -> None:
    missing = point("c1", error=0.01)
    missing.invariant_error = None
    assert compensation.select_weak_points(
        [missing], error_threshold=0.1, error_metric="invariant_error"
    ) == [missing]


def test_numerical_divergence_is_selected_but_execution_failures_are_not() -> None:
    crashed = point("c1", error=0.0, status=Status.CRASHED)
    timeout = point("c2", error=0.0, status=Status.TIMEOUT)
    diverged = point("c3", error=0.0, status=Status.DIVERGED)
    assert compensation.select_weak_points([crashed, timeout, diverged]) == [diverged]


def test_catastrophic_measurement_is_preserved_but_not_repaired() -> None:
    catastrophic = point("c1", error=0.5, status=Status.DIVERGED)
    catastrophic.numerically_catastrophic = True
    catastrophic.accuracy_band = "catastrophic"
    assert compensation.select_weak_points([catastrophic], error_threshold=0.01) == []
    assert compensation.select_weak_points(
        [catastrophic], error_threshold=0.01, include_catastrophic=True
    ) == [catastrophic]


def test_weak_points_share_one_portable_group_per_candidate_and_precision() -> None:
    cuda = point("c1", error=0.4)
    cuda.backend = "cuda"
    groq = point("c1", error=0.5)
    groq.backend = "groq"
    other = point("c2", error=0.6)
    groups = compensation.group_portable_weak_points([groq, other, cuda])
    assert [[point.backend for point in group] for group in groups] == [
        ["groq", "cuda"],
        ["cpu"],
    ]


class NoOpSession:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    async def send(self, _: str) -> HermesTurn:
        return HermesTurn('{"technique":"kahan","summary":"comments only"}', Usage())

    async def close(self) -> None:
        return None


def test_noop_compensation_is_rejected_before_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = minimal_config(tmp_path)
    data["compensation"] = {"correction_rounds": 0}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)
    module = tmp_path / "base.py"
    module.write_text(GOOD_MODULE)
    base = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    weak = point("c1", error=0.4)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    oracle = OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def unexpected_validation(*_: object, **__: object) -> object:
        raise AssertionError("no-op variant should not reach external validation")

    monkeypatch.setattr(compensation, "HermesSession", NoOpSession)
    monkeypatch.setattr(compensation, "validate_candidate", unexpected_validation)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    async def run() -> compensation.CompensationVariant:
        async with await ExecutionContext.start(
            config, run_dir, hermes_home=tmp_path / "hermes"
        ) as execution:
            return await compensation.generate_compensation(
                config,
                oracle,
                run_dir,
                execution,
                base,
                [weak],
                [config.measure.backends[0]],
            )

    variant = asyncio.run(run())
    assert variant.status == Status.REJECTED
    assert variant.diagnostics[0].gate == "compensation-change"


class EditingSession:
    def __init__(self, *_: object, **kwargs: Any) -> None:
        self.cwd = kwargs["cwd"]
        self.turn = 0

    async def send(self, _: str) -> HermesTurn:
        self.turn += 1
        target = self.cwd / "candidate.py"
        source = target.read_text()
        target.write_text(source.replace("return x\n", f"return x + {self.turn} * 0\n"))
        return HermesTurn('{"technique":"kahan","summary":"edited"}', Usage())

    async def close(self) -> None:
        return None


def test_saved_repair_revalidates_against_staged_baseline_without_model_turn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    base_path = tmp_path / "base.py"
    base_path.write_text(GOOD_MODULE)
    saved_path = tmp_path / "saved.py"
    saved_source = GOOD_MODULE.replace("return x\n", "return x + 0\n")
    saved_path.write_text(saved_source)
    base = Candidate("c1", "model", None, "direct", base_path, status=Status.OK)
    previous = compensation.CompensationVariant(
        "c1",
        "n-c1-fp16",
        "portable",
        "fp16",
        "kahan",
        saved_path,
        status=Status.REJECTED,
        usage=Usage(input_tokens=123),
    )

    class SavedSession(NoOpSession):
        async def send(self, _: str) -> HermesTurn:
            raise AssertionError("a valid saved edit must not consume a model turn")

    class Execution:
        def workspace_dir(self, slug: str) -> Path:
            return tmp_path / slug

        def register_workspace(self, slug: str) -> str:
            return slug

        def backend(self) -> object:
            return self

        async def stage_bytes(self, slug: str, name: str, data: bytes) -> None:
            destination = self.workspace_dir(slug) / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)

        async def mirror_file(self, *_: object) -> None:
            pass

    execution = Execution()

    async def accepted(*_: object, **__: object) -> ValidationResult:
        return ValidationResult(True, None, np.asarray([1.0, 2.0, 3.0]))

    async def collapse(
        config: object,
        backend: object,
        base_workspace: str,
        compensated_workspace: str,
        diagnostic_dir: Path,
        **kwargs: Any,
    ) -> ValidationResult:
        assert base_workspace == compensated_workspace == "n-c1-fp16"
        assert kwargs["base_module"] == ".lassi/baseline.py"
        assert (
            execution.workspace_dir(base_workspace) / kwargs["base_module"]
        ).read_text() == GOOD_MODULE
        assert (
            execution.workspace_dir(base_workspace) / "candidate.py"
        ).read_text() == saved_source
        return await accepted()

    monkeypatch.setattr(compensation, "HermesSession", SavedSession)
    monkeypatch.setattr(compensation, "validate_candidate", accepted)
    monkeypatch.setattr(compensation, "validate_fp32_collapse", collapse)
    oracle = OracleResult(tmp_path / "oracle.npy", np.asarray([1.0, 2.0, 3.0]))
    variant = asyncio.run(
        compensation.generate_compensation(
            config,
            oracle,
            tmp_path,
            cast("ExecutionContext", execution),
            base,
            [point("c1", error=0.5)],
            [config.measure.backends[0]],
            previous=previous,
        )
    )
    assert variant.status == Status.OK
    assert variant.usage.input_tokens == 123
    assert not variant.diagnostics


class ImprovingBackend(Backend[Any]):
    def __init__(self, spec: BackendConfig) -> None:
        super().__init__(spec)
        self.errors = iter([0.6, 0.1])

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
        error = next(self.errors)
        return Measurement(
            kernel="tiny",
            candidate_id=candidate_id,
            variant_id=variant_id,
            backend=self.spec.name,
            precision=precision,
            compensation=compensation,
            status=Status.OK,
            module_path="candidate.py",
            storage_precision=precision,
            operator_precision=precision,
            accumulator_precision=precision,
            output_precision=precision,
            source_hash="fixture-source",
            precision_verdict="passed",
            precision_audit_protocol="executed-dtype-v3",
            precision_audit_source_hash="fixture-source",
            latency_s=1.0,
            max_rel_error=error,
            relative_l2=error,
            evaluation_output_checked=True,
            evaluation_output_finite=True,
            evaluation_semantic_verified=True,
            accuracy_source="timed_device_workload",
        )


def test_target_measurement_feedback_stays_in_compensation_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = minimal_config(tmp_path)
    data["compensation"] = {"correction_rounds": 1}
    (tmp_path / "tiny.c").write_text("int main(void) { return 0; }")
    config = RunConfig.model_validate(data)
    base_path = tmp_path / "base.py"
    base_path.write_text(GOOD_MODULE)
    base = Candidate("c1", "model", None, "direct", base_path, status=Status.OK)
    weak = point("c1", error=0.5)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    oracle = OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def accepted(*_: object, **__: object) -> ValidationResult:
        return ValidationResult(True, None, np.asarray([1.0, 2.0, 3.0]))

    monkeypatch.setattr(compensation, "HermesSession", EditingSession)
    monkeypatch.setattr(compensation, "validate_candidate", accepted)
    monkeypatch.setattr(compensation, "validate_fp32_collapse", accepted)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    async def run() -> compensation.CompensationVariant:
        async with await ExecutionContext.start(
            config, run_dir, hermes_home=tmp_path / "hermes"
        ) as execution:
            return await compensation.generate_compensation(
                config,
                oracle,
                run_dir,
                execution,
                base,
                [weak],
                [config.measure.backends[0]],
                {"cpu": ImprovingBackend(config.measure.backends[0])},
            )

    variant = asyncio.run(run())
    assert variant.status == Status.OK
    assert variant.correction_rounds == 1
    assert variant.backend == "portable"
    assert variant.target_backends == ["cpu"]
    assert [item.status for item in variant.target_measurements] == [Status.OK, Status.OK]
    assert [item.max_rel_error for item in variant.target_measurements] == [0.6, 0.1]
