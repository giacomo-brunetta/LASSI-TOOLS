from __future__ import annotations

import asyncio
import hashlib
import math
import statistics
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..config import BackendConfig
from ..types import Measurement, Status

if TYPE_CHECKING:
    from pathlib import Path

    from ..config import RunConfig
    from ..validation import OracleResult

_ARCHITECTURAL_TIMING_PROTOCOL = "architectural-single-call-v1"
_ARCHITECTURAL_TIMING_EXCLUDES = {
    "allocation",
    "compilation",
    "device_attach",
    "device_to_host",
    "executable_load",
    "host_to_device",
    "queue",
}

def _timing_fields(timing: dict[str, Any]) -> dict[str, Any]:
    """Map worker timing evidence into the stable measurement schema."""

    raw_samples = timing.get("samples_s") or []
    try:
        samples = [float(value) for value in raw_samples]
    except (TypeError, ValueError):
        samples = []
    raw_excludes = timing.get("excludes") or []
    excludes = (
        [str(value) for value in raw_excludes]
        if isinstance(raw_excludes, (list, tuple, set))
        else []
    )

    def optional_int(name: str) -> int | None:
        value = timing.get(name)
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    return {
        "latency_scope": str(timing.get("scope") or ""),
        "latency_source": str(timing.get("source") or ""),
        "latency_clock": str(timing.get("clock") or ""),
        "timing_protocol": str(timing.get("protocol") or ""),
        "timing_warmup_count": optional_int("warmup_count"),
        "timing_sample_count": optional_int("sample_count"),
        "timing_invocations_per_sample": optional_int("invocations_per_sample"),
        "timing_samples_s": samples,
        "timing_physical_device_count": optional_int("physical_device_count"),
        "timing_input_residency": str(timing.get("input_residency") or ""),
        "timing_output_residency_at_stop": str(timing.get("output_residency_at_stop") or ""),
        "timing_excludes": excludes,
        "latency_includes_input_construction": bool(
            timing.get("includes_input_construction", False)
        ),
        "latency_cuda_synchronized": bool(timing.get("cuda_synchronized", False)),
    }

def _architectural_timing_error(measurement: Measurement) -> str | None:
    """Return why a purported architectural accelerator latency is incomparable."""

    if measurement.timing_protocol != _ARCHITECTURAL_TIMING_PROTOCOL:
        return f"timing protocol must be {_ARCHITECTURAL_TIMING_PROTOCOL}"
    if measurement.latency_scope != "device_resident_graph":
        return "latency scope must be device_resident_graph"
    if not measurement.latency_source or not measurement.latency_clock:
        return "a native device timing source and clock are required"
    if measurement.latency_clock in {"time.perf_counter", "time.monotonic", "host_clock"}:
        return "host clocks cannot measure architectural accelerator latency"
    if measurement.timing_warmup_count is None or measurement.timing_warmup_count < 1:
        return "at least one untimed warmup invocation is required"
    if measurement.timing_invocations_per_sample != 1:
        return "each timing sample must contain exactly one graph invocation"
    if measurement.timing_physical_device_count != 1:
        return "each timing cell must use exactly one physical accelerator"
    if measurement.timing_input_residency != "device":
        return "inputs must be resident on the accelerator before timing starts"
    if measurement.timing_output_residency_at_stop != "device":
        return "timing must stop when the output is ready on the accelerator"
    missing = sorted(_ARCHITECTURAL_TIMING_EXCLUDES - set(measurement.timing_excludes))
    if missing:
        return "timing did not exclude: " + ", ".join(missing)
    samples = measurement.timing_samples_s
    if measurement.timing_sample_count != len(samples) or not samples:
        return "timing sample count is missing or inconsistent"
    if any(not math.isfinite(value) or value <= 0 for value in samples):
        return "timing samples must be finite positive seconds"
    expected_median = statistics.median(samples)
    if measurement.latency_s is None or not math.isclose(
        measurement.latency_s, expected_median, rel_tol=1e-12, abs_tol=1e-15
    ):
        return "latency_s must be the median of the single-call samples"
    if measurement.min_s is None or not math.isclose(
        measurement.min_s, min(samples), rel_tol=1e-12, abs_tol=1e-15
    ):
        return "min_s must be the minimum of the single-call samples"
    return None

def _enforce_architectural_timing(measurement: Measurement) -> Measurement:
    """Reject accelerator latency that does not satisfy the comparison contract."""

    if measurement.status != Status.OK or measurement.latency_s is None:
        return measurement
    error = _architectural_timing_error(measurement)
    if error is None:
        return measurement
    measurement.status = Status.CRASHED
    measurement.failure_kind = "incomparable_timing"
    measurement.notes = f"{measurement.notes}; latency was rejected: {error}".strip("; ")
    return measurement

class _SubmitTimeoutError(Exception):
    """Raised when staging or submitting remote work exceeds the submit deadline.

    Distinct from the execution timeout: this means the request never reached a
    worker, so no job exists to poll or cancel.
    """

    def __init__(self, stage: str, limit_s: float) -> None:
        super().__init__(f"{stage} exceeded the {limit_s:g}s submit deadline")
        self.stage = stage
        self.limit_s = limit_s

class Backend[BackendConfigT: BackendConfig](ABC):
    def __init__(
        self,
        spec: BackendConfigT,
        *,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        self.spec = spec
        self.semaphore = semaphore or asyncio.Semaphore(1)

    def supports(self, precision: str) -> bool:
        return precision in self.spec.precisions

    @abstractmethod
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
    ) -> Measurement: ...

def _base_measurement(
    config: RunConfig,
    spec: BackendConfig,
    module_path: Path,
    candidate_id: str,
    variant_id: str,
    precision: str,
    compensation: str,
    status: Status,
    **kwargs: Any,
) -> Measurement:
    evaluation_dataset = config.evaluation_dataset
    return Measurement(
        kernel=config.kernel.name,
        candidate_id=candidate_id,
        variant_id=variant_id,
        backend=spec.name,
        precision=precision,
        compensation=compensation,
        status=status,
        module_path=str(module_path),
        storage_precision=precision,
        operator_precision=precision,
        accumulator_precision=precision,
        output_precision=precision,
        error_metric=config.pareto_error_metric,
        evaluation_dataset=evaluation_dataset,
        source_hash=(
            hashlib.sha256(module_path.read_bytes()).hexdigest() if module_path.is_file() else ""
        ),
        **kwargs,
    )

def _evaluation_oracle_path(config: RunConfig, oracle: OracleResult) -> Path:
    """Return the oracle matching the workload used for both accuracy and timing."""

    if config.evaluation_dataset == config.kernel.validation_dataset:
        return oracle.output_path
    if config.evaluation_oracle is None:
        raise ValueError("distinct accelerator evaluation dataset requires evaluation_oracle")
    return config.resolve_project_path(config.evaluation_oracle)

def _enforce_accuracy_latency_pair(measurement: Measurement) -> Measurement:
    """Reject successful latency records lacking device-derived evaluation accuracy."""

    if measurement.status != Status.OK or measurement.latency_s is None:
        return measurement
    paired = (
        measurement.y_error is not None
        and measurement.evaluation_output_checked
        and measurement.evaluation_output_finite is True
        and measurement.evaluation_semantic_verified
        and bool(measurement.accuracy_source)
    )
    if paired:
        return measurement
    measurement.status = Status.DIVERGED
    measurement.failure_kind = "missing_accuracy_latency_pair"
    measurement.notes = (
        f"{measurement.notes}; latency was rejected because the timed workload did not "
        "produce a finite device accuracy measurement against its oracle"
    ).strip("; ")
    return measurement
