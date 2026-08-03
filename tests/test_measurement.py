from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from types import SimpleNamespace
from typing import TYPE_CHECKING

import numpy as np
import yaml

import lassi_x.measurement as measurement
from lassi_x.config import BackendConfig, RunConfig
from lassi_x.measurement import Backend, GroqBackend
from lassi_x.types import Measurement, Status
from lassi_x.validation import OracleResult

from .test_config import minimal_config

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def setup_run(tmp_path: Path) -> tuple[RunConfig, Path, OracleResult]:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    config = RunConfig.load(config_path)
    module = tmp_path / "candidate.py"
    module.write_text("# source\n")
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0]))
    return config, module, OracleResult(oracle_path, np.asarray([1.0]))


def groq_spec(queue: Path) -> BackendConfig:
    return BackendConfig(
        type="groq",
        name="groq",
        queue_dir=queue,
        precisions=["fp16"],
        timeout_s=1,
        healthcheck_max_age_s=10,
        stale_request_s=60,
    )


def test_groq_backend_fails_fast_without_live_worker(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    started = time.monotonic()
    result = asyncio.run(
        GroqBackend(groq_spec(tmp_path / "queue")).measure(
            config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp16",
            compensation="none",
        )
    )
    assert time.monotonic() - started < 0.5
    assert result.status == Status.TIMEOUT
    assert "health check failed" in result.notes


def test_groq_queue_completion_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, module, oracle = setup_run(tmp_path)
    queue = tmp_path / "queue"
    (queue / "completed").mkdir(parents=True)
    (queue / "worker-heartbeat.json").write_text("{}")
    request_id = "fixed-request"
    (queue / "completed" / f"{request_id}.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "request_id": request_id,
                "status": "ok",
                "latency_s": 0.001,
                "max_rel_error": 0.02,
            }
        )
    )
    monkeypatch.setattr(uuid, "uuid4", lambda: SimpleNamespace(hex=request_id))
    result = asyncio.run(
        GroqBackend(groq_spec(queue)).measure(
            config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp16",
            compensation="none",
        )
    )
    assert result.status == Status.OK
    assert result.latency_s == 0.001
    assert result.max_rel_error == 0.02


def test_stale_groq_requests_are_reaped(tmp_path: Path) -> None:
    queue = tmp_path / "queue"
    pending = queue / "pending"
    pending.mkdir(parents=True)
    request = pending / "old.json"
    request.write_text('{"request_id":"old"}')
    old = time.time() - 100
    os.utime(request, (old, old))
    measurement._reap_stale_groq_requests(queue, stale_after_s=10)
    result = json.loads((queue / "completed" / "old.json").read_text())
    assert result["status"] == "timeout"
    assert not request.exists()


class RecordingBackend(Backend):
    def __init__(self, spec: BackendConfig) -> None:
        super().__init__(spec)
        self.calls: list[str] = []

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
        del oracle, seed
        self.calls.append(precision)
        return measurement._base_measurement(
            config,
            self.spec,
            module_path,
            candidate_id,
            variant_id,
            precision,
            compensation,
            Status.OK,
            latency_s=1.0,
            max_rel_error=0.0,
        )


def test_compensation_measurement_defaults_to_target_cell(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    cpu = RecordingBackend(config.measure.backends[0])
    other_spec = config.measure.backends[0].model_copy(update={"name": "other"})
    other = RecordingBackend(other_spec)
    results = asyncio.run(
        measurement.measure_compensation_variants(
            config,
            oracle,
            [("c1", "variant", module, "kahan", "cpu", "fp16")],
            [cpu, other],
        )
    )
    assert len(results) == 1
    assert cpu.calls == ["fp16"]
    assert other.calls == []
