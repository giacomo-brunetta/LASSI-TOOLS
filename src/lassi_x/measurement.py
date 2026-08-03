from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import statistics
import time
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .execution import put_bytes
from .protocol import ExecRequest
from .types import Measurement, Status
from .validation import fixture_relative_path

if TYPE_CHECKING:
    from pathlib import Path

    from .config import BackendConfig, RunConfig
    from .execution import ExecutionBackend, ExecutionContext
    from .validation import OracleResult

_DEVICE_ACCELERATORS = {"cuda": "cuda", "xpu": "xpu", "mps": "mps"}


class Backend(ABC):
    def __init__(
        self,
        spec: BackendConfig,
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
        source_hash=(
            hashlib.sha256(module_path.read_bytes()).hexdigest() if module_path.is_file() else ""
        ),
        **kwargs,
    )


class TorchBackend(Backend):
    """Measure latency/error cells by running the worker on one resource.

    The candidate module, oracle output, and fixture are pushed into a
    measurement workspace on the backing execution resource, so the worker
    (and the accelerator it exercises) runs wherever the resource lives while
    the harness only orchestrates and records.
    """

    def __init__(
        self,
        spec: BackendConfig,
        execution: ExecutionBackend,
        resource: str,
        *,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        """Configure the backend.

        Args:
            spec: Measurement backend configuration.
            execution: Execution backend of the resource that runs the worker.
            resource: Resource name recorded on measurements.
            semaphore: Optional shared lock used to isolate timing-sensitive torch work.

        """
        super().__init__(spec, semaphore=semaphore)
        self.execution = execution
        self.resource = resource
        self._staged_workspaces: set[str] = set()

    def _device_available(self, handshake_kinds: set[str]) -> bool:
        """Check the configured device against the resource's accelerators."""
        prefix = str(self.spec.device).partition(":")[0]
        required = _DEVICE_ACCELERATORS.get(prefix)
        return required is None or required in handshake_kinds

    async def _stage_inputs(
        self, config: RunConfig, oracle: OracleResult, workspace: str, module_path: Path
    ) -> str:
        """Push the module, oracle, and fixture into the measurement workspace.

        Static inputs (oracle, fixture) are pushed once per workspace; the
        module is pushed on every call because variants share workspaces
        across attempts.

        Args:
            config: Validated run configuration.
            oracle: Authoritative oracle whose output file the worker compares against.
            workspace: Measurement workspace identifier.
            module_path: Harness-local module to measure.

        Returns:
            The workspace-relative oracle path to pass to the worker.

        """
        oracle_name = f"oracle{oracle.output_path.suffix or '.dat'}"
        await put_bytes(self.execution, workspace, module_path.name, module_path.read_bytes())
        if workspace not in self._staged_workspaces:
            await put_bytes(
                self.execution,
                workspace,
                oracle_name,
                oracle.output_path.read_bytes(),
            )
            fixture = fixture_relative_path(config)
            if fixture is not None and config.oracle.input_fixture is not None:
                source = config.resolve_project_path(config.oracle.input_fixture)
                await put_bytes(self.execution, workspace, fixture, source.read_bytes())
            self._staged_workspaces.add(workspace)
        return oracle_name

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
        if not self.supports(precision):
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.UNSUPPORTED,
                resource=self.resource,
            )
        handshake = await self.execution.cached_handshake()
        if not self._device_available({item.kind for item in handshake.accelerators}):
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.UNSUPPORTED,
                resource=self.resource,
                notes=f"device {self.spec.device} is unavailable on resource {self.resource}",
            )
        workspace = "m-" + re.sub(r"[^A-Za-z0-9._-]", "-", variant_id)[:60]
        oracle_name = await self._stage_inputs(config, oracle, workspace, module_path)
        command = [
            handshake.python_executable,
            "-m",
            "lassi_x.measure_worker",
            "--module",
            module_path.name,
            "--oracle",
            oracle_name,
            "--device",
            str(self.spec.device),
            "--precision",
            precision,
            "--warmup",
            str(config.measure.warmup),
            "--iterations",
            str(config.measure.iterations),
            "--rtol",
            str(config.arena.equivalence.rtol),
            "--atol",
            str(config.arena.equivalence.atol),
            "--seed",
            str(seed),
        ]
        fixture = fixture_relative_path(config)
        if fixture is not None:
            command += ["--fixture", fixture]
        if config.kernel.invariant:
            command += ["--invariant", config.kernel.invariant]
        if config.kernel.invariant_threshold is not None:
            command += [
                "--invariant-threshold",
                str(config.kernel.invariant_threshold),
            ]
        if precision in config.measure.strict_precisions:
            command.append("--require-equivalence")
        async with self.semaphore:
            result = await self.execution.execute(
                ExecRequest(workspace=workspace, argv=command, timeout_s=self.spec.timeout_s)
            )
        if result.timed_out:
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.TIMEOUT,
                resource=self.resource,
                notes="measurement timed out",
            )
        try:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            payload = {"ok": False, "error": (result.stderr or result.stdout)[-2000:]}
        if result.exit_code != 0 or not payload.get("ok"):
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.CRASHED,
                resource=self.resource,
                notes=str(payload.get("error") or "measurement worker failed"),
            )
        metrics = payload.get("metrics") or {}
        precision_meta = payload.get("precision") or {}
        timing_meta = payload.get("timing") or {}
        measurement = _base_measurement(
            config,
            self.spec,
            module_path,
            candidate_id,
            variant_id,
            precision,
            compensation,
            Status.OK if payload.get("valid", payload.get("equivalent")) else Status.DIVERGED,
            resource=self.resource,
            latency_s=float(payload["median_s"]),
            min_s=float(payload["min_s"]),
            latency_scope=str(timing_meta.get("scope", "model_forward")),
            latency_source=str(timing_meta.get("source", "remote_measure_worker")),
            latency_clock=str(timing_meta.get("clock", "time.perf_counter")),
            latency_includes_input_construction=bool(
                timing_meta.get("includes_input_construction", False)
            ),
            latency_cuda_synchronized=bool(
                timing_meta.get("cuda_synchronized", str(self.spec.device).startswith("cuda"))
            ),
            max_abs_error=metrics.get("max_abs_error"),
            max_rel_error=metrics.get("max_rel_error"),
            relative_l2=metrics.get("relative_l2"),
            invariant_error=payload.get("invariant_error"),
            invariant_candidate=payload.get("invariant_candidate") or {},
            notes=(
                ""
                if payload.get("equivalent")
                else "measured low-precision error: "
                + json.dumps(payload.get("diagnostic"), default=str)
            ),
        )
        measurement.storage_precision = str(precision_meta.get("storage", precision))
        measurement.operator_precision = str(precision_meta.get("operator", precision))
        measurement.accumulator_precision = str(precision_meta.get("accumulator", precision))
        measurement.output_precision = str(precision_meta.get("output", precision))
        return measurement


class GroqBackend(Backend):
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
        if not self.supports(precision):
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.UNSUPPORTED,
            )
        queue = self.spec.queue_dir
        assert queue is not None
        for subdir in ("pending", "running", "completed"):
            (queue / subdir).mkdir(parents=True, exist_ok=True)
        _reap_stale_groq_requests(queue, self.spec.stale_request_s)
        heartbeat = queue / "worker-heartbeat.json"
        try:
            heartbeat_age = time.time() - heartbeat.stat().st_mtime
        except FileNotFoundError:
            heartbeat_age = None
        if heartbeat_age is None or heartbeat_age > self.spec.healthcheck_max_age_s:
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.TIMEOUT,
                notes=(
                    "Groq worker health check failed before submission; "
                    f"heartbeat max age is {self.spec.healthcheck_max_age_s:g}s"
                ),
            )
        request_id = uuid.uuid4().hex
        request = {
            "schema_version": 1,
            "request_id": request_id,
            "module_path": str(module_path.resolve()),
            "oracle_path": str(oracle.output_path.resolve()),
            "kernel": config.kernel.name,
            "candidate_id": candidate_id,
            "variant_id": variant_id,
            "precision": precision,
            "compensation": compensation,
            "seed": seed,
        }
        temporary = queue / "pending" / f".{request_id}.tmp"
        destination = queue / "pending" / f"{request_id}.json"
        temporary.write_text(json.dumps(request))
        os.replace(temporary, destination)
        result_path = queue / "completed" / f"{request_id}.json"
        deadline = time.monotonic() + self.spec.timeout_s
        while time.monotonic() < deadline:
            if result_path.is_file():
                try:
                    payload = json.loads(result_path.read_text())
                except (OSError, json.JSONDecodeError) as exc:
                    return _base_measurement(
                        config,
                        self.spec,
                        module_path,
                        candidate_id,
                        variant_id,
                        precision,
                        compensation,
                        Status.CRASHED,
                        notes=f"invalid Groq completion record: {type(exc).__name__}: {exc}",
                    )
                status_raw = payload.get("status", "crashed")
                try:
                    status = Status(status_raw)
                except ValueError:
                    status = Status.CRASHED
                return _base_measurement(
                    config,
                    self.spec,
                    module_path,
                    candidate_id,
                    variant_id,
                    precision,
                    compensation,
                    status,
                    latency_s=payload.get("latency_s"),
                    max_abs_error=payload.get("max_abs_error"),
                    max_rel_error=payload.get("max_rel_error"),
                    relative_l2=payload.get("relative_l2"),
                    invariant_error=payload.get("invariant_error"),
                    notes=str(payload.get("notes") or ""),
                )
            await asyncio.sleep(0.5)
        destination.unlink(missing_ok=True)
        return _base_measurement(
            config,
            self.spec,
            module_path,
            candidate_id,
            variant_id,
            precision,
            compensation,
            Status.TIMEOUT,
            notes="Groq worker did not return before timeout",
        )


def _reap_stale_groq_requests(queue: Path, stale_after_s: float) -> None:
    """Convert abandoned pending/running requests into timeout completions.

    Args:
        queue: Root directory of the filesystem queue.
        stale_after_s: Maximum request-file age before it is considered abandoned.

    """
    now = time.time()
    completed = queue / "completed"
    completed.mkdir(parents=True, exist_ok=True)
    for state in ("pending", "running"):
        for request_path in (queue / state).glob("*.json"):
            try:
                age = now - request_path.stat().st_mtime
                if age <= stale_after_s:
                    continue
                request = json.loads(request_path.read_text())
                request_id = str(request.get("request_id") or request_path.stem)
                result = {
                    "schema_version": 1,
                    "request_id": request_id,
                    "status": Status.TIMEOUT.value,
                    "notes": f"reaped stale Groq {state} request after {age:.1f}s",
                }
                temporary = completed / f".{request_id}.tmp"
                temporary.write_text(json.dumps(result, indent=2) + "\n")
                os.replace(temporary, completed / f"{request_id}.json")
                request_path.unlink(missing_ok=True)
            except (OSError, json.JSONDecodeError):
                continue


def build_backends(config: RunConfig, execution: ExecutionContext) -> list[Backend]:
    """Instantiate one measurement backend per configured cell provider.

    Args:
        config: Validated run configuration.
        execution: Running execution context supplying per-resource backends.

    Returns:
        The measurement backends, with torch backends bound to the execution
        resource named by their ``resource`` field (default resource when
        omitted).

    """
    result: list[Backend] = []
    torch_lock = asyncio.Semaphore(1) if config.measure.serialize_torch_backends else None
    for spec in config.measure.backends:
        if spec.type == "torch":
            resource = spec.resource or execution.default_resource
            result.append(
                TorchBackend(
                    spec,
                    execution.backend(spec.resource),
                    resource,
                    semaphore=torch_lock,
                )
            )
        else:
            result.append(GroqBackend(spec))
    return result


async def measure_variants(
    config: RunConfig,
    oracle: OracleResult,
    variants: list[tuple[str, str, Path, str]],
    backends: list[Backend],
) -> list[Measurement]:
    calls = []
    for candidate_id, variant_id, module_path, compensation in variants:
        for backend in backends:
            for precision in config.measure.precisions:
                calls.append(
                    backend.measure(
                        config,
                        oracle,
                        module_path,
                        candidate_id=candidate_id,
                        variant_id=variant_id,
                        precision=precision,
                        compensation=compensation,
                    )
                )
    return list(await asyncio.gather(*calls))


async def measure_compensation_variants(
    config: RunConfig,
    oracle: OracleResult,
    variants: list[tuple[str, str, Path, str, str, str]],
    backends: list[Backend],
) -> list[Measurement]:
    """Measure generated variants, sampling stochastic rounding across configured seeds."""
    results: list[Measurement] = []
    for (
        candidate_id,
        variant_id,
        module_path,
        compensation,
        target_backend,
        target_precision,
    ) in variants:
        selected_backends = (
            backends
            if config.compensation.measurement_scope == "all"
            else [backend for backend in backends if backend.spec.name == target_backend]
        )
        precisions = (
            config.measure.precisions
            if config.compensation.measurement_scope == "all"
            else [target_precision]
        )
        for backend in selected_backends:
            for precision in precisions:
                seeds = (
                    config.measure.stochastic_seeds if compensation == "stochastic-round" else [0]
                )
                samples = await asyncio.gather(
                    *(
                        backend.measure(
                            config,
                            oracle,
                            module_path,
                            candidate_id=candidate_id,
                            variant_id=variant_id,
                            precision=precision,
                            compensation=compensation,
                            seed=seed,
                        )
                        for seed in seeds
                    )
                )
                primary = samples[0]
                if len(samples) > 1:
                    primary.stochastic_samples = [
                        {
                            "seed": seed,
                            "status": sample.status.value,
                            "latency_s": sample.latency_s,
                            "max_rel_error": sample.max_rel_error,
                            "relative_l2": sample.relative_l2,
                        }
                        for seed, sample in zip(seeds, samples, strict=False)
                    ]
                    valid_latencies = [
                        sample.latency_s for sample in samples if sample.latency_s is not None
                    ]
                    valid_rel = [
                        sample.max_rel_error
                        for sample in samples
                        if sample.max_rel_error is not None
                    ]
                    if valid_latencies:
                        primary.latency_s = statistics.median(valid_latencies)
                    if valid_rel:
                        primary.max_rel_error = statistics.mean(valid_rel)
                    if any(sample.status != Status.OK for sample in samples):
                        primary.status = Status.DIVERGED
                results.append(primary)
    return results
