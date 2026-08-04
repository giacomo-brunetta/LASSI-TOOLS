from __future__ import annotations

import asyncio
import json
import os
import shlex
import time
import uuid
from types import SimpleNamespace
from typing import TYPE_CHECKING

import numpy as np
import pytest
import yaml

import lassi_x.measurement as measurement
from lassi_x.config import BackendConfig, RunConfig
from lassi_x.execution import LocalExecutionBackend
from lassi_x.measurement import Backend, GroqBackend, TorchBackend
from lassi_x.protocol import ExecRequest, ExecResult
from lassi_x.types import Measurement, Status
from lassi_x.validation import OracleResult, build_oracle

from .test_config import minimal_config
from .test_validation import C_REFERENCE, GOOD_MODULE

if TYPE_CHECKING:
    from pathlib import Path


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


def _setup_torch(tmp_path: Path) -> tuple[RunConfig, OracleResult, Path]:
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    config = RunConfig.load(config_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    return config, oracle, module


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


class FakePBSExecutionBackend(LocalExecutionBackend):
    """Synthesize a compute-node result while recording the PBS request."""

    def __init__(self, workspace_root: Path) -> None:
        super().__init__(workspace_root, "groq-login")
        self.requests: list[ExecRequest] = []

    async def execute(self, request: ExecRequest) -> ExecResult:
        """Record qsub and materialize the result named by its job script."""
        self.requests.append(request)
        script = (self.workspace_root / request.workspace / request.argv[-1]).read_text()
        command = shlex.split(script.splitlines()[-1])
        output_name = command[command.index("--output") + 1]
        result_path = self.workspace_root / request.workspace / output_name
        result_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "valid": True,
                    "equivalent": False,
                    "diagnostic": {"gate": "equivalence"},
                    "median_s": 0.000123,
                    "min_s": 0.000123,
                    "metrics": {
                        "max_abs_error": 0.01,
                        "max_rel_error": 0.02,
                        "relative_l2": 0.003,
                    },
                    "timing": {
                        "scope": "model_forward",
                        "source": "groq_sdk_benchmark",
                        "clock": "groq_runtime",
                        "includes_input_construction": False,
                    },
                    "precision": {
                        "storage": "fp16",
                        "operator": "fp16",
                        "accumulator": "groq-backend-defined",
                        "output": "fp16",
                    },
                }
            )
        )
        return ExecResult(
            workspace=request.workspace,
            exit_code=0,
            stdout="12345.groq-r01-control\n",
            duration_s=1.0,
        )


def test_groq_pbs_backend_uses_academy_and_sdk_latency(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = BackendConfig.model_validate(
        {
            "type": "groq",
            "name": "groq-lpu",
            "resource": "groq-login",
            "precisions": ["fp16"],
            "timeout_s": 60,
            "pbs": {
                "conda_sh": "/shared/miniconda3/etc/profile.d/conda.sh",
                "conda_env": "groqflow",
                "python": "/shared/miniconda3/envs/groqflow/bin/python",
                "pythonpath": ["/shared/LASSI-TOOLS/src"],
            },
        }
    )
    execution = FakePBSExecutionBackend(tmp_path / "remote")
    result = asyncio.run(
        GroqBackend(spec, execution, "groq-login").measure(
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
    assert result.resource == "groq-login"
    assert result.latency_s == 0.000123
    assert result.latency_source == "groq_sdk_benchmark"
    assert result.worker_wall_s is None
    request = execution.requests[0]
    assert request.argv[0] == "/opt/pbs/bin/qsub"
    assert "select=1,place=excl" in request.argv
    job_script = (tmp_path / "remote" / "groq-c1-base" / request.argv[-1]).read_text()
    assert "conda activate groqflow" in job_script
    assert "--accuracy-dataset default" in job_script
    assert "--performance-dataset default" in job_script
    assert (tmp_path / "remote" / "groq-c1-base" / "groq_measure_worker.py").is_file()


def test_groq_pbs_transactions_are_serialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = BackendConfig.model_validate(
        {
            "type": "groq",
            "name": "groq-lpu",
            "resource": "groq-login",
            "precisions": ["fp16"],
            "pbs": {
                "conda_sh": "/shared/conda.sh",
                "python": "/shared/groqflow/bin/python",
            },
        }
    )
    backend = GroqBackend(spec, LocalExecutionBackend(tmp_path / "remote"), "groq-login")
    active = 0
    maximum = 0

    async def fake_measure(*_args: object, **_kwargs: object) -> object:
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.01)
        active -= 1
        return object()

    monkeypatch.setattr(backend, "_measure_pbs", fake_measure)

    async def run() -> None:
        await asyncio.gather(
            *(
                backend.measure(
                    config,
                    oracle,
                    module,
                    candidate_id=f"c{index}",
                    variant_id=f"c{index}-base",
                    precision="fp16",
                    compensation="none",
                )
                for index in range(3)
            )
        )

    asyncio.run(run())
    assert maximum == 1


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


def test_torch_backend_measures_through_execution_backend(tmp_path: Path) -> None:
    config, oracle, module = _setup_torch(tmp_path)
    execution_root = tmp_path / "exec"
    backend = TorchBackend(
        config.measure.backends[0], LocalExecutionBackend(execution_root, "here"), "here"
    )
    result = asyncio.run(
        backend.measure(
            config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp64",
            compensation="none",
        )
    )
    assert result.status == Status.OK
    assert result.resource == "here"
    assert result.latency_s is not None and result.latency_s > 0
    assert result.worker_wall_s is None
    assert result.latency_scope == "model_forward"
    assert result.latency_source == "remote_measure_worker"
    assert result.latency_clock == "time.perf_counter"
    assert result.latency_includes_input_construction is False
    assert result.latency_cuda_synchronized is False
    workspace = execution_root / "m-c1-base"
    assert (workspace / "candidate.py").is_file()
    assert (workspace / "oracle.csv").is_file()


def test_torch_backend_reports_unavailable_device_from_handshake(tmp_path: Path) -> None:
    config, oracle, module = _setup_torch(tmp_path)
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0]["device"] = "cuda:0"
    cuda_config = RunConfig.model_validate(data)
    backend = TorchBackend(
        cuda_config.measure.backends[0],
        LocalExecutionBackend(tmp_path / "exec", "cpu-box"),
        "cpu-box",
    )
    result = asyncio.run(
        backend.measure(
            cuda_config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp64",
            compensation="none",
        )
    )
    if result.status == Status.OK:
        pytest.skip("host actually has CUDA")
    assert result.status == Status.UNSUPPORTED
    assert "cpu-box" in result.notes


def test_backend_resource_must_be_configured(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0]["resource"] = "nvidia"
    with pytest.raises(ValueError, match="unknown execution resources"):
        RunConfig.model_validate(data)
    data["execution"] = {"mode": "academy", "resources": {"nvidia": {}}}
    assert RunConfig.model_validate(data).measure.backends[0].resource == "nvidia"
