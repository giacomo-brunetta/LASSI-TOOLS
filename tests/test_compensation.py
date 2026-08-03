from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import numpy as np
import yaml

import lassi_x.compensation as compensation
from lassi_x.config import RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.hermes import HermesTurn
from lassi_x.types import Candidate, Measurement, Status, Usage
from lassi_x.validation import OracleResult

from .test_config import minimal_config
from .test_validation import GOOD_MODULE

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


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
        latency_s=latency,
        max_rel_error=error,
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


def test_failed_low_precision_point_is_selected_but_timeout_is_not() -> None:
    crashed = point("c1", error=0.0, status=Status.CRASHED)
    timeout = point("c2", error=0.0, status=Status.TIMEOUT)
    assert compensation.select_weak_points([crashed, timeout]) == [crashed]


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
                weak,
                config.measure.backends[0],
            )

    variant = asyncio.run(run())
    assert variant.status == Status.REJECTED
    assert variant.diagnostics[0].gate == "compensation-change"
