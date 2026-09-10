from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import os
import shlex
import sys
import time
import uuid
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import yaml

import lassi_x.measurement as measurement
from lassi_x.config import (
    BackendConfig,
    GroqBackendConfig,
    NativeBackendConfig,
    RunConfig,
    TorchBackendConfig,
)
from lassi_x.execution import LocalExecutionBackend
from lassi_x.measurement import Backend, GroqBackend, NativeBackend, TorchBackend
from lassi_x.protocol import ExecRequest, ExecResult
from lassi_x.types import Measurement, Status
from lassi_x.validation import OracleResult, build_oracle, compare_outputs

from .test_config import minimal_config
from .test_validation import C_REFERENCE, GOOD_MODULE

if TYPE_CHECKING:
    from pathlib import Path


def architectural_timing(samples: list[float] | None = None) -> dict[str, Any]:
    values = samples or [0.000123]
    return {
        "protocol": "architectural-single-call-v1",
        "scope": "device_resident_graph",
        "source": "native_device_timer",
        "clock": "device_clock",
        "includes_input_construction": False,
        "warmup_count": 3,
        "sample_count": len(values),
        "invocations_per_sample": 1,
        "samples_s": values,
        "physical_device_count": 1,
        "input_residency": "device",
        "output_residency_at_stop": "device",
        "excludes": [
            "allocation",
            "compilation",
            "device_attach",
            "device_to_host",
            "executable_load",
            "host_to_device",
            "queue",
        ],
    }


def setup_run(tmp_path: Path) -> tuple[RunConfig, Path, OracleResult]:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    config = RunConfig.load(config_path)
    module = tmp_path / "candidate.py"
    module.write_text("# source\n")
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0]))
    return config, module, OracleResult(oracle_path, np.asarray([1.0]))


def test_groq_relative_error_uses_the_same_near_zero_scale_as_torch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_groqflow = ModuleType("groqflow")
    fake_groqflow.groqit = lambda model: model  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "groqflow", fake_groqflow)
    compare_groq_outputs = importlib.import_module("lassi_x.groq_measure_worker")._compare

    candidate = np.asarray([1e-8])
    oracle = np.asarray([0.0])
    groq = compare_groq_outputs(candidate, oracle, rtol=1e-3, atol=1e-6)
    _, _, torch_metrics = compare_outputs(
        candidate,
        oracle,
        rtol=1e-3,
        atol=1e-6,
        max_mismatches=1,
    )
    assert groq["metrics"]["max_rel_error"] == pytest.approx(torch_metrics["max_rel_error"])


def groq_spec(queue: Path) -> GroqBackendConfig:
    return GroqBackendConfig(
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
                "min_s": 0.001,
                "max_rel_error": 0.02,
                "accuracy_checked": True,
                "accuracy_finite": True,
                "accuracy_numel": 1,
                "accuracy_sha256": "abc",
                "accuracy_oracle_compared": True,
                "accuracy_source": "timed_device_workload",
                "timing": architectural_timing([0.001]),
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
                    "timing": architectural_timing(),
                    "precision": {
                        "storage": "fp16",
                        "operator": "fp16",
                        "accumulator": "groq-backend-defined",
                        "output": "fp16",
                    },
                    "evaluation_output": {
                        "checked": True,
                        "finite": True,
                        "numel": 1,
                        "sha256": "abc",
                        "semantic_verified": True,
                        "accuracy_source": "same_compiled_model_and_inputs",
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


class FakeNativeExecutionBackend(LocalExecutionBackend):
    """Return a conforming native-device record without importing a vendor SDK."""

    async def execute(self, request: ExecRequest) -> ExecResult:
        workspace = self.workspace_root / request.workspace
        output_name = request.argv[request.argv.index("--output") + 1]
        module_name = request.argv[request.argv.index("--module") + 1]
        candidate = workspace / module_name
        payload = {
            "ok": True,
            "valid": True,
            "equivalent": True,
            "median_s": 0.000123,
            "min_s": 0.000123,
            "metrics": {"max_abs_error": 0.0, "max_rel_error": 0.0, "relative_l2": 0.0},
            "timing": architectural_timing(),
            "precision": {
                "storage": "fp16",
                "operator": "fp16",
                "accumulator": "fp32",
                "output": "fp16",
                "observed_output": "float16",
            },
            "source_hash": hashlib.sha256(candidate.read_bytes()).hexdigest(),
            "evaluation_output": {
                "checked": True,
                "finite": True,
                "numel": 1,
                "sha256": "abc",
                "semantic_verified": True,
                "accuracy_source": "timed_device_invocation",
            },
        }
        (workspace / output_name).write_text(json.dumps(payload))
        return ExecResult(workspace=request.workspace, exit_code=0, stdout="", duration_s=10.0)


def test_native_backend_accepts_only_device_clock_single_call_records(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = NativeBackendConfig.model_validate(
        {
            "type": "native",
            "name": "graphcore-ipu",
            "architecture": "graphcore_ipu",
            "resource": "graphcore",
            "precisions": ["fp16"],
            "worker": {"python": "/opt/poplar/bin/python"},
        }
    )
    execution = FakeNativeExecutionBackend(tmp_path / "remote", "graphcore")
    result = asyncio.run(
        NativeBackend(spec, execution, "graphcore").measure(
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
    assert result.latency_s == 0.000123
    assert result.worker_wall_s is None
    assert result.timing_protocol == "architectural-single-call-v1"
    assert result.timing_invocations_per_sample == 1
    assert result.timing_physical_device_count == 1
    assert (tmp_path / "remote" / "native-c1-base" / "native_measure_worker.py").is_file()


def test_architectural_timing_rejects_amortized_latency() -> None:
    point = Measurement(
        kernel="tiny",
        candidate_id="c1",
        variant_id="c1-base",
        backend="accelerator",
        precision="fp16",
        compensation="none",
        status=Status.OK,
        module_path="candidate.py",
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        latency_s=0.001,
        min_s=0.001,
        timing_protocol="architectural-single-call-v1",
        latency_scope="device_resident_graph",
        latency_source="native_device_timer",
        latency_clock="device_clock",
        timing_warmup_count=3,
        timing_sample_count=1,
        timing_invocations_per_sample=20,
        timing_samples_s=[0.001],
        timing_physical_device_count=1,
        timing_input_residency="device",
        timing_output_residency_at_stop="device",
        timing_excludes=list(architectural_timing()["excludes"]),
    )
    rejected = measurement._enforce_architectural_timing(point)
    assert rejected.status == Status.CRASHED
    assert rejected.failure_kind == "incomparable_timing"
    assert "exactly one graph invocation" in rejected.notes


def test_architectural_timing_rejects_host_clock() -> None:
    point = Measurement(
        kernel="tiny",
        candidate_id="c1",
        variant_id="c1-base",
        backend="accelerator",
        precision="fp16",
        compensation="none",
        status=Status.OK,
        module_path="candidate.py",
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        latency_s=0.000123,
        min_s=0.000123,
        timing_protocol="architectural-single-call-v1",
        latency_scope="device_resident_graph",
        latency_source="host_stopwatch",
        latency_clock="time.perf_counter",
        timing_warmup_count=3,
        timing_sample_count=1,
        timing_invocations_per_sample=1,
        timing_samples_s=[0.000123],
        timing_physical_device_count=1,
        timing_input_residency="device",
        timing_output_residency_at_stop="device",
        timing_excludes=list(architectural_timing()["excludes"]),
    )
    rejected = measurement._enforce_architectural_timing(point)
    assert rejected.status == Status.CRASHED
    assert "host clocks cannot" in rejected.notes


def test_groq_pbs_backend_uses_academy_and_sdk_latency(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = GroqBackendConfig.model_validate(
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
                "pythonpath": ["/shared/LASSI-TOOLS"],
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
    assert result.latency_source == "native_device_timer"
    assert result.worker_wall_s is None
    request = execution.requests[0]
    assert request.argv[0] == "/opt/pbs/bin/qsub"
    assert "select=1,place=excl" in request.argv
    job_script = (tmp_path / "remote" / "groq-c1-base" / request.argv[-1]).read_text()
    assert "conda activate groqflow" in job_script
    assert "--dataset default" in job_script
    assert "--accuracy-dataset" not in job_script
    assert "--performance-dataset" not in job_script
    # GroqRack exports /opt/groq/runtime/site-packages site-wide, which precedes the
    # conda env on sys.path and shadows it; the worker must not inherit that.
    assert job_script.index("unset PYTHONPATH") < job_script.index("conda activate")
    assert (tmp_path / "remote" / "groq-c1-base" / "groq_measure_worker.py").is_file()


def test_groq_direct_mode_runs_the_worker_without_pbs(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = GroqBackendConfig.model_validate(
        {
            "type": "groq",
            "name": "groq-lpu",
            "resource": "groq-compute",
            "precisions": ["fp16"],
            "timeout_s": 60,
            "runtime": {
                "conda_sh": "/shared/miniconda3/etc/profile.d/conda.sh",
                "conda_env": "groqflow",
                "python": "/shared/miniconda3/envs/groqflow/bin/python",
                "pythonpath": ["/shared/LASSI-TOOLS"],
            },
        }
    )
    execution = FakePBSExecutionBackend(tmp_path / "remote")
    result = asyncio.run(
        GroqBackend(spec, execution, "groq-compute").measure(
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
    assert result.resource == "groq-compute"
    assert result.latency_s == 0.000123
    request = execution.requests[0]
    # The worker runs in place; no batch system is involved.
    assert request.argv[0] == "bash"
    assert not any("qsub" in argument for argument in request.argv)
    script = (tmp_path / "remote" / "groq-c1-base" / request.argv[-1]).read_text()
    assert "conda activate groqflow" in script
    assert "--dataset default" in script
    assert script.index("unset PYTHONPATH") < script.index("conda activate")


class StalledExecutionBackend(LocalExecutionBackend):
    """Model an endpoint that heartbeats but never claims a submitted task."""

    async def execute(self, request: ExecRequest) -> ExecResult:
        """Never return, the way an unclaimed Globus Compute task never returns."""
        del request
        await asyncio.sleep(3600)
        raise AssertionError("unreachable")


def test_groq_submission_deadline_bounds_an_unclaimed_task(tmp_path: Path) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = GroqBackendConfig.model_validate(
        {
            "type": "groq",
            "name": "groq-lpu",
            "resource": "groq-login",
            "precisions": ["fp16"],
            # Execution may wait hours in the PBS queue; submission may not.
            "timeout_s": 7200,
            "submit_timeout_s": 0.25,
            "pbs": {
                "conda_sh": "/shared/miniconda3/etc/profile.d/conda.sh",
                "conda_env": "groqflow",
                "python": "/shared/miniconda3/envs/groqflow/bin/python",
            },
        }
    )
    backend = GroqBackend(
        spec, StalledExecutionBackend(tmp_path / "remote", "groq-login"), "groq-login"
    )
    started = time.monotonic()
    result = asyncio.run(
        backend.measure(
            config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp16",
            compensation="none",
        )
    )
    elapsed = time.monotonic() - started
    assert result.status == Status.TIMEOUT
    # The cell must fail on submit_timeout_s, not the 7200s execution ceiling.
    assert elapsed < 30.0
    # The note must name the stalled stage and say no job was created, so an
    # unreachable endpoint is not mistaken for a slow PBS queue.
    assert "submit deadline" in (result.notes or "")
    assert "No PBS job was created" in (result.notes or "")
    assert "no free worker" in (result.notes or "")


def test_groq_pbs_transactions_are_serialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, module, oracle = setup_run(tmp_path)
    spec = GroqBackendConfig.model_validate(
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


class RecordingBackend(Backend[BackendConfig]):
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


def test_portable_compensation_is_broadcast_to_every_cell(tmp_path: Path) -> None:
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
    assert len(results) == 4
    assert cpu.calls == ["fp64", "fp32"]
    assert other.calls == ["fp64", "fp32"]


def test_torch_backend_measures_through_execution_backend(tmp_path: Path) -> None:
    config, oracle, module = _setup_torch(tmp_path)
    execution_root = tmp_path / "exec"
    spec = config.measure.backends[0]
    assert isinstance(spec, TorchBackendConfig)
    backend = TorchBackend(
        spec, LocalExecutionBackend(execution_root, "here"), "here"
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
    assert result.latency_scope == "host_model_forward"
    assert result.latency_source == "remote_measure_worker"
    assert result.latency_clock == "time.perf_counter"
    assert result.latency_includes_input_construction is False
    assert result.latency_cuda_synchronized is False
    assert result.evaluation_output_checked is True
    assert result.evaluation_output_finite is True
    assert result.evaluation_output_numel == 3
    assert len(result.evaluation_output_sha256) == 64
    assert result.source_integrity_verified is True
    assert result.accuracy_source == "timed_iteration"
    assert result.evaluation_dataset == "default"
    workspace = execution_root / "m-c1-base"
    assert (workspace / "candidate.py").is_file()
    assert (workspace / "oracle.csv").is_file()


def test_distinct_evaluation_dataset_is_checked_against_external_oracle(
    tmp_path: Path,
) -> None:
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    evaluation_oracle = tmp_path / "evaluation.csv"
    evaluation_oracle.write_text("1\n2\n3\n")
    data = minimal_config(tmp_path)
    data["kernel"]["validation_dataset"] = "mini"
    data["measure"]["evaluation_dataset"] = "large"
    data["measure"]["evaluation_oracle"] = "evaluation.csv"
    config = RunConfig.model_validate(data)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    spec = config.measure.backends[0]
    assert isinstance(spec, TorchBackendConfig)
    backend = TorchBackend(
        spec,
        LocalExecutionBackend(tmp_path / "exec", "here"),
        "here",
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
    assert result.evaluation_semantic_verified is True
    assert result.evaluation_dataset == "large"


def test_torch_backend_reports_unavailable_device_from_handshake(tmp_path: Path) -> None:
    config, oracle, module = _setup_torch(tmp_path)
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0]["device"] = "cuda:0"
    cuda_config = RunConfig.model_validate(data)
    spec = cuda_config.measure.backends[0]
    assert isinstance(spec, TorchBackendConfig)
    backend = TorchBackend(
        spec,
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
