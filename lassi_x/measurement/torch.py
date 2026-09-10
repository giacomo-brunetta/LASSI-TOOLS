from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING

from ..config import TorchBackendConfig
from ..execution import RemoteCallTimeoutError, put_bytes
from ..protocol import ExecRequest
from ..types import Measurement, Status
from ..validation import fixture_relative_path
from .common import (
    Backend,
    _base_measurement,
    _enforce_accuracy_latency_pair,
    _enforce_architectural_timing,
    _evaluation_oracle_path,
    _timing_fields,
)

if TYPE_CHECKING:
    import asyncio
    from pathlib import Path

    from ..config import RunConfig
    from ..execution import ExecutionBackend
    from ..validation import OracleResult

_DEVICE_ACCELERATORS = {"cuda": "cuda", "xpu": "xpu", "mps": "mps"}

class TorchBackend(Backend[TorchBackendConfig]):
    """Measure latency/error cells by running the worker on one resource.

    The candidate module, oracle output, and fixture are pushed into a
    measurement workspace on the backing execution resource, so the worker
    (and the accelerator it exercises) runs wherever the resource lives while
    the harness only orchestrates and records.
    """

    def __init__(
        self,
        spec: TorchBackendConfig,
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
        """Push the module, merged-evaluation oracle, and fixture into the workspace.

        Static inputs (oracle, fixture) are pushed once per workspace; the
        module is pushed on every call because variants share workspaces
        across attempts.

        Args:
            config: Validated run configuration.
            oracle: Authoritative oracle whose output file the worker compares against.
            workspace: Measurement workspace identifier.
            module_path: Harness-local module to measure.

        Returns:
            Workspace-relative oracle path for the workload that is timed.

        """
        evaluation_oracle = _evaluation_oracle_path(config, oracle)
        oracle_name = f"oracle{evaluation_oracle.suffix or '.dat'}"
        await put_bytes(self.execution, workspace, module_path.name, module_path.read_bytes())
        if workspace not in self._staged_workspaces:
            await put_bytes(
                self.execution,
                workspace,
                oracle_name,
                evaluation_oracle.read_bytes(),
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
        """Measure one variant, degrading to a timeout cell if the agent is mute.

        An unreachable execution agent is a property of the resource, not of
        the candidate under test. Recording it as a timeout keeps the rest of
        the matrix running and leaves the affected cells identifiable, rather
        than aborting the run on the first unanswered call.
        """
        try:
            return await self._measure(
                config,
                oracle,
                module_path,
                candidate_id=candidate_id,
                variant_id=variant_id,
                precision=precision,
                compensation=compensation,
                seed=seed,
            )
        except RemoteCallTimeoutError as exc:
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
                failure_kind="infrastructure_timeout",
                notes=f"execution agent unreachable: {exc}",
            )

    async def _measure(
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
                failure_kind="precision_unsupported",
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
                failure_kind="resource_unavailable",
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
            "--dataset",
            config.evaluation_dataset,
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
                failure_kind="execution_timeout",
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
                failure_kind=str(payload.get("phase") or "worker_execution"),
                notes=str(payload.get("error") or "measurement worker failed"),
            )
        expected_source_hash = hashlib.sha256(module_path.read_bytes()).hexdigest()
        reported_source_hash = str(payload.get("source_hash") or "")
        if reported_source_hash and reported_source_hash != expected_source_hash:
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
                failure_kind="source_integrity",
                notes="measurement worker executed a different candidate source hash",
            )
        metrics = payload.get("metrics") or {}
        precision_meta = payload.get("precision") or {}
        timing_meta = payload.get("timing") or {}
        evaluation_meta = payload.get("evaluation_output") or {}
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
            **_timing_fields(timing_meta),
            max_abs_error=metrics.get("max_abs_error"),
            max_rel_error=metrics.get("max_rel_error"),
            relative_l2=metrics.get("relative_l2"),
            invariant_error=payload.get("invariant_error"),
            invariant_candidate=payload.get("invariant_candidate") or {},
            failure_kind=(
                "" if payload.get("valid", payload.get("equivalent")) else "numerical_divergence"
            ),
            evaluation_output_checked=bool(evaluation_meta.get("checked", False)),
            evaluation_output_finite=evaluation_meta.get("finite"),
            evaluation_output_numel=evaluation_meta.get("numel"),
            evaluation_output_sha256=str(evaluation_meta.get("sha256") or ""),
            evaluation_semantic_verified=bool(evaluation_meta.get("semantic_verified", False)),
            accuracy_source=str(evaluation_meta.get("accuracy_source") or ""),
            source_integrity_verified=reported_source_hash == expected_source_hash,
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
        measurement.observed_output_precision = str(precision_meta.get("observed_output", ""))
        measurement.precision_metadata_source = str(
            precision_meta.get("metadata_source", "candidate_declared")
        )
        measurement = _enforce_accuracy_latency_pair(measurement)
        if str(self.spec.device).startswith("cuda"):
            measurement = _enforce_architectural_timing(measurement)
        return measurement
