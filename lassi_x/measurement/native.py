from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..config import NativeBackendConfig
from ..execution import RemoteCallTimeoutError, fetch_bytes, put_bytes
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

    from ..config import RunConfig
    from ..execution import ExecutionBackend
    from ..validation import OracleResult

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent

class NativeBackend(Backend[NativeBackendConfig]):
    """Run a standalone Graphcore or Cerebras measurement worker on its resource.

    The worker owns compilation and deployment because those operations are
    site/toolchain specific. Only its native device-clock record crosses the
    measurement boundary; orchestration wall time is never used as latency.
    """

    def __init__(
        self,
        spec: NativeBackendConfig,
        execution: ExecutionBackend,
        resource: str,
        *,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        super().__init__(spec, semaphore=semaphore)
        self.execution = execution
        self.resource = resource

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
                failure_kind="precision_unsupported",
            )
        worker = self.spec.worker
        architecture = self.spec.architecture
        assert worker is not None and architecture is not None
        workspace = "native-" + re.sub(r"[^A-Za-z0-9._-]", "-", variant_id)[:52]
        evaluation_oracle = _evaluation_oracle_path(config, oracle)
        oracle_name = f"oracle{evaluation_oracle.suffix or '.dat'}"
        worker_name = "native_measure_worker.py"
        output_name = f"result-{uuid.uuid4().hex}.json"
        if worker.script is None:
            worker_source = _PACKAGE_ROOT / "graphcore_measure_worker.py"
        else:
            worker_source = config.resolve_project_path(worker.script)
        try:
            await put_bytes(self.execution, workspace, "candidate.py", module_path.read_bytes())
            await put_bytes(
                self.execution,
                workspace,
                oracle_name,
                evaluation_oracle.read_bytes(),
            )
            await put_bytes(self.execution, workspace, worker_name, worker_source.read_bytes())
            fixture = fixture_relative_path(config)
            if fixture is not None and config.oracle.input_fixture is not None:
                source = config.resolve_project_path(config.oracle.input_fixture)
                await put_bytes(self.execution, workspace, fixture, source.read_bytes())
        except (OSError, RemoteCallTimeoutError) as exc:
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
                failure_kind="worker_staging",
                notes=f"native worker staging failed: {type(exc).__name__}: {exc}",
            )
        command = [
            str(worker.python),
            worker_name,
            "--architecture",
            architecture,
            "--module",
            "candidate.py",
            "--oracle",
            oracle_name,
            "--output",
            output_name,
            "--precision",
            precision,
            "--dataset",
            config.evaluation_dataset,
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
        if precision in config.measure.strict_precisions:
            command.append("--require-equivalence")
        async with self.semaphore:
            try:
                result = await self.execution.execute(
                    ExecRequest(workspace=workspace, argv=command, timeout_s=self.spec.timeout_s)
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
                notes="native accelerator worker timed out",
            )
        try:
            payload: Any = json.loads(await fetch_bytes(self.execution, workspace, output_name))
        except (OSError, ValueError, json.JSONDecodeError):
            payload = {
                "ok": False,
                "error": (result.stderr or result.stdout)[-2000:]
                or "native accelerator worker produced no result file",
            }
        return self._finalize(
            payload,
            config,
            module_path,
            candidate_id=candidate_id,
            variant_id=variant_id,
            precision=precision,
            compensation=compensation,
        )

    def _finalize(
        self,
        payload: Any,
        config: RunConfig,
        module_path: Path,
        *,
        candidate_id: str,
        variant_id: str,
        precision: str,
        compensation: str,
    ) -> Measurement:
        """Validate one native worker record and convert it to a measurement."""

        if not isinstance(payload, dict) or not payload.get("ok"):
            detail = payload if isinstance(payload, dict) else {}
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
                failure_kind=str(detail.get("phase") or "worker_protocol"),
                notes=str(detail.get("error") or "native worker returned an invalid record"),
            )
        expected_hash = hashlib.sha256(module_path.read_bytes()).hexdigest()
        reported_hash = str(payload.get("source_hash") or "")
        if reported_hash != expected_hash:
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
                notes="native worker did not prove the measured candidate source hash",
            )
        timing = payload.get("timing") or {}
        metrics = payload.get("metrics") or {}
        precision_meta = payload.get("precision") or {}
        evaluation = payload.get("evaluation_output") or {}
        try:
            latency_s = float(payload["median_s"])
            min_s = float(payload["min_s"])
        except (KeyError, TypeError, ValueError):
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
                failure_kind="worker_protocol",
                notes="native worker omitted finite median_s/min_s timing values",
            )
        valid = bool(payload.get("valid", payload.get("equivalent")))
        measurement = _base_measurement(
            config,
            self.spec,
            module_path,
            candidate_id,
            variant_id,
            precision,
            compensation,
            Status.OK if valid else Status.DIVERGED,
            resource=self.resource,
            latency_s=latency_s,
            min_s=min_s,
            **_timing_fields(timing),
            max_abs_error=metrics.get("max_abs_error"),
            max_rel_error=metrics.get("max_rel_error"),
            relative_l2=metrics.get("relative_l2"),
            failure_kind="" if valid else "numerical_divergence",
            evaluation_output_checked=bool(evaluation.get("checked", False)),
            evaluation_output_finite=evaluation.get("finite"),
            evaluation_output_numel=evaluation.get("numel"),
            evaluation_output_sha256=str(evaluation.get("sha256") or ""),
            evaluation_semantic_verified=bool(evaluation.get("semantic_verified", False)),
            accuracy_source=str(evaluation.get("accuracy_source") or ""),
            source_integrity_verified=True,
            notes=(
                ""
                if payload.get("equivalent")
                else "measured device error: " + json.dumps(payload.get("diagnostic"), default=str)
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
        return _enforce_architectural_timing(measurement)
