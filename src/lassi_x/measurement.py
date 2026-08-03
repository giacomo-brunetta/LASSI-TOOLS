from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import signal
import statistics
import sys
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .types import Measurement, Status

if TYPE_CHECKING:
    from .config import BackendConfig, RunConfig
    from .validation import OracleResult


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
        if str(self.spec.device).startswith("cuda"):
            try:
                # Avoid importing Torch in orchestration processes without CUDA work.
                import torch  # noqa: PLC0415

                cuda_available = torch.cuda.is_available()
            except ImportError:
                cuda_available = False
            if not cuda_available:
                return _base_measurement(
                    config,
                    self.spec,
                    module_path,
                    candidate_id,
                    variant_id,
                    precision,
                    compensation,
                    Status.UNSUPPORTED,
                    notes="CUDA is unavailable",
                )
        command = [
            sys.executable,
            "-m",
            "lassi_x.measure_worker",
            "--module",
            str(module_path),
            "--oracle",
            str(oracle.output_path),
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
        if config.oracle.input_fixture:
            command += [
                "--fixture",
                str(config.resolve_project_path(config.oracle.input_fixture)),
            ]
        if config.kernel.invariant:
            command += ["--invariant", config.kernel.invariant]
        if config.kernel.invariant_threshold is not None:
            command += [
                "--invariant-threshold",
                str(config.kernel.invariant_threshold),
            ]
        if precision in config.measure.strict_precisions:
            command.append("--require-equivalence")
        env = os.environ.copy()
        package_root = str(Path(__file__).resolve().parents[1])
        env["PYTHONPATH"] = (
            package_root
            + os.pathsep
            + str(config.project.root)
            + os.pathsep
            + env.get("PYTHONPATH", "")
        )
        async with self.semaphore:
            worker_started = time.perf_counter()
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=module_path.parent,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.spec.timeout_s
                )
            except TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                await process.wait()
                return _base_measurement(
                    config,
                    self.spec,
                    module_path,
                    candidate_id,
                    variant_id,
                    precision,
                    compensation,
                    Status.TIMEOUT,
                    worker_wall_s=time.perf_counter() - worker_started,
                    notes="measurement timed out",
                )
        try:
            payload = json.loads(stdout.decode().strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            payload = {"ok": False, "error": stderr.decode(errors="replace")[-2000:]}
        if process.returncode or not payload.get("ok"):
            return _base_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                Status.CRASHED,
                worker_wall_s=time.perf_counter() - worker_started,
                notes=str(payload.get("error") or "measurement worker failed"),
            )
        metrics = payload.get("metrics") or {}
        precision_meta = payload.get("precision") or {}
        measurement = _base_measurement(
            config,
            self.spec,
            module_path,
            candidate_id,
            variant_id,
            precision,
            compensation,
            Status.OK if payload.get("valid", payload.get("equivalent")) else Status.DIVERGED,
            latency_s=float(payload["median_s"]),
            min_s=float(payload["min_s"]),
            worker_wall_s=time.perf_counter() - worker_started,
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


def build_backends(config: RunConfig) -> list[Backend]:
    result: list[Backend] = []
    torch_lock = asyncio.Semaphore(1) if config.measure.serialize_torch_backends else None
    for spec in config.measure.backends:
        result.append(
            TorchBackend(spec, semaphore=torch_lock) if spec.type == "torch" else GroqBackend(spec)
        )
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
