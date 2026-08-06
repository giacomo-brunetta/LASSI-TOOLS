from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import re
import shlex
import statistics
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .execution import RemoteCallTimeoutError, fetch_bytes, put_bytes
from .protocol import ExecRequest
from .types import Measurement, Status
from .validation import fixture_relative_path

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from .config import BackendConfig, GroqRuntimeConfig, RunConfig
    from .execution import ExecutionBackend, ExecutionContext
    from .validation import OracleResult

_DEVICE_ACCELERATORS = {"cuda": "cuda", "xpu": "xpu", "mps": "mps"}


class _SubmitTimeoutError(Exception):
    """Raised when staging or submitting remote work exceeds the submit deadline.

    Distinct from the execution timeout: this means the request never reached a
    worker, so no job exists to poll or cancel.
    """

    def __init__(self, stage: str, limit_s: float) -> None:
        super().__init__(f"{stage} exceeded the {limit_s:g}s submit deadline")
        self.stage = stage
        self.limit_s = limit_s


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


def _runtime_prelude(runtime: GroqRuntimeConfig) -> list[str]:
    """Open a worker script with a clean interpreter environment.

    ``PYTHONPATH`` is cleared before conda is sourced rather than merely
    overwritten. Entries on it precede the environment's own ``site-packages``
    in ``sys.path``, so a site-wide export such as GroqRack's
    ``/opt/groq/runtime/site-packages`` shadows the conda environment and
    breaks imports before any of our code runs.

    Args:
        runtime: Interpreter settings for the measurement worker.

    Returns:
        Script lines up to and including the environment setup.
    """
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "unset PYTHONPATH",
        f"source {shlex.quote(str(runtime.conda_sh))}",
        f"conda activate {shlex.quote(runtime.conda_env)}",
    ]
    if runtime.pythonpath:
        lines.append(
            "export PYTHONPATH=" + shlex.quote(":".join(str(path) for path in runtime.pythonpath))
        )
    return lines


def _submit_timeout_measurement(
    config: RunConfig,
    spec: BackendConfig,
    module_path: Path,
    candidate_id: str,
    variant_id: str,
    precision: str,
    compensation: str,
    resource: str,
    exc: _SubmitTimeoutError,
) -> Measurement:
    """Record a cell whose work never reached a worker.

    Args:
        config: Active run configuration.
        spec: Backend that failed to submit.
        module_path: Candidate module under measurement.
        candidate_id: Arena candidate identifier.
        variant_id: Base or compensated variant identifier.
        precision: Requested precision.
        compensation: Compensation label recorded in provenance.
        resource: Execution resource name recorded in provenance.
        exc: Deadline breach describing which stage stalled.

    Returns:
        Timeout measurement whose note names the stalled stage, so an
        unreachable endpoint is distinguishable from a slow PBS queue.
    """
    return _base_measurement(
        config,
        spec,
        module_path,
        candidate_id,
        variant_id,
        precision,
        compensation,
        Status.TIMEOUT,
        resource=resource,
        notes=(
            f"Groq submission stalled: {exc}. No PBS job was created. The execution "
            "endpoint is most likely online but has no free worker to claim the task."
        ),
    )


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
        accuracy_dataset=config.kernel.validation_dataset,
        performance_dataset=config.measure.performance_dataset,
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
            "--accuracy-dataset",
            config.kernel.validation_dataset,
            "--performance-dataset",
            config.measure.performance_dataset,
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
    """Measure Groq either through a legacy queue or Academy plus PBS."""

    def __init__(
        self,
        spec: BackendConfig,
        execution: ExecutionBackend | None = None,
        resource: str = "",
        *,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        """Bind an optional Academy resource used to submit PBS jobs.

        Args:
            spec: Groq backend configuration.
            execution: Login-node execution backend for direct PBS mode.
            resource: Resource name recorded in measurement provenance.
            semaphore: Lock serializing exclusive-node Groq measurements.
        """
        super().__init__(spec, semaphore=semaphore)
        self.execution = execution
        self.resource = resource
        self._transaction_semaphore = asyncio.Semaphore(1)

    async def _bounded(self, stage: str, awaitable: Awaitable[Any]) -> Any:
        """Await one staging or submission RPC under the submit deadline.

        An :class:`ExecRequest` timeout is enforced by the worker that runs it,
        so it never fires while the task sits unclaimed on an endpoint that is
        heartbeating but has no free worker. This bound is enforced locally.

        Args:
            stage: Short label naming the RPC, used in the failure note.
            awaitable: Coroutine performing the RPC.

        Returns:
            Whatever the awaited coroutine returns.

        Raises:
            _SubmitTimeoutError: The deadline expired before the RPC completed.
        """
        try:
            return await asyncio.wait_for(awaitable, self.spec.submit_timeout_s)
        except TimeoutError:
            raise _SubmitTimeoutError(stage, self.spec.submit_timeout_s) from None

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
        if self.execution is not None:
            # One Academy execution agent serves the resource. Keep staging,
            # launch, and polling for each cell together so concurrent candidate
            # fan-out cannot interleave multiple RPC streams on that agent.
            launch = self._measure_pbs if self.spec.pbs is not None else self._measure_direct
            try:
                async with self._transaction_semaphore:
                    return await launch(
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
                # A mute agent is a resource fault, not a candidate fault:
                # record the cell and let the rest of the matrix proceed.
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
                    notes=f"execution agent unreachable: {exc}",
                )
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

    async def _measure_direct(
        self,
        config: RunConfig,
        oracle: OracleResult,
        module_path: Path,
        *,
        candidate_id: str,
        variant_id: str,
        precision: str,
        compensation: str,
        seed: int,
    ) -> Measurement:
        """Stage and measure one candidate in place on a GroqRack compute node.

        Used when the execution endpoint already runs on a node that owns LPUs,
        so no batch job is needed. This removes the PBS queue entirely: the
        worker starts as soon as the endpoint claims the task. As in PBS mode,
        only the SDK's on-LPU benchmark latency is reported.

        Args:
            config: Validated run configuration.
            oracle: External C FP64 oracle generated by the harness.
            module_path: Candidate module in the harness artifact tree.
            candidate_id: Arena candidate identifier.
            variant_id: Base or compensated variant identifier.
            precision: Requested precision; GroqFlow mode supports FP16.
            compensation: Compensation label recorded in provenance.
            seed: Deterministic measurement seed, retained for interface parity.

        Returns:
            Structured measurement populated from the compute-node worker.
        """
        del seed
        if not self.supports(precision) or precision != "fp16":
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
                notes="GroqFlow hardware execution is configured for FP16",
            )
        runtime = self.spec.runtime
        assert runtime is not None
        assert self.execution is not None
        workspace = "groq-" + re.sub(r"[^A-Za-z0-9._-]", "-", variant_id)[:54]
        oracle_name = f"oracle{oracle.output_path.suffix or '.dat'}"
        worker_name = "groq_measure_worker.py"
        request_id = uuid.uuid4().hex
        result_name = f"result-{request_id}.json"
        script_name = f"run-{request_id}.sh"
        source_hash = hashlib.sha256(module_path.read_bytes()).hexdigest()
        try:
            handshake = await self._bounded("handshake", self.execution.cached_handshake())
            await self._bounded(
                "stage candidate",
                put_bytes(self.execution, workspace, "candidate.py", module_path.read_bytes()),
            )
            await self._bounded(
                "stage oracle",
                put_bytes(self.execution, workspace, oracle_name, oracle.output_path.read_bytes()),
            )
            await self._bounded(
                "stage worker",
                put_bytes(
                    self.execution,
                    workspace,
                    worker_name,
                    Path(__file__).with_name(worker_name).read_bytes(),
                ),
            )
            remote_workspace = Path(handshake.workspace_root) / workspace
            command = [
                str(runtime.python),
                worker_name,
                "--module",
                "candidate.py",
                "--oracle",
                oracle_name,
                "--output",
                result_name,
                "--iterations",
                str(config.measure.iterations),
                "--rtol",
                str(config.arena.equivalence.rtol),
                "--atol",
                str(config.arena.equivalence.atol),
                "--cache-dir",
                str(remote_workspace / "groq-cache" / source_hash[:16]),
                "--build-name",
                f"lassi-{variant_id}-{source_hash[:12]}",
                "--accuracy-dataset",
                config.kernel.validation_dataset,
                "--performance-dataset",
                config.measure.performance_dataset,
            ]
            script_lines = _runtime_prelude(runtime)
            script_lines.extend([f"cd {shlex.quote(str(remote_workspace))}", shlex.join(command)])
            await self._bounded(
                "stage run script",
                put_bytes(
                    self.execution,
                    workspace,
                    script_name,
                    ("\n".join(script_lines) + "\n").encode(),
                ),
            )
        except _SubmitTimeoutError as exc:
            return _submit_timeout_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                self.resource,
                exc,
            )
        async with self.semaphore:
            result = await self.execution.execute(
                ExecRequest(
                    workspace=workspace,
                    argv=["bash", script_name],
                    timeout_s=self.spec.timeout_s,
                )
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
                notes=f"Groq direct worker exceeded {self.spec.timeout_s:g}s on the compute node",
            )
        try:
            payload: Any = json.loads(await fetch_bytes(self.execution, workspace, result_name))
        except (OSError, ValueError, json.JSONDecodeError):
            payload = {
                "ok": False,
                "error": (result.stderr or result.stdout)[-2000:]
                or "Groq direct worker produced no result file",
            }
        return self._finalize(
            payload,
            config,
            module_path,
            candidate_id=candidate_id,
            variant_id=variant_id,
            precision=precision,
            compensation=compensation,
            mode="direct",
        )

    async def _measure_pbs(
        self,
        config: RunConfig,
        oracle: OracleResult,
        module_path: Path,
        *,
        candidate_id: str,
        variant_id: str,
        precision: str,
        compensation: str,
        seed: int,
    ) -> Measurement:
        """Stage and measure one candidate in an exclusive Groq PBS job.

        The Academy execution agent remains on the Groq login node. PBS owns
        placement on a GroqRack compute node, where the job activates the
        configured GroqFlow environment. Only the SDK's on-LPU benchmark
        latency is accepted; Academy, PBS, and input-construction time never
        enter the reported latency.

        Args:
            config: Validated run configuration.
            oracle: External C FP64 oracle generated by the harness.
            module_path: Candidate module in the harness artifact tree.
            candidate_id: Arena candidate identifier.
            variant_id: Base or compensated variant identifier.
            precision: Requested precision; GroqFlow mode supports FP16.
            compensation: Compensation label recorded in provenance.
            seed: Deterministic measurement seed, retained for interface parity.

        Returns:
            Structured measurement populated from the compute-node worker.
        """
        del seed
        if not self.supports(precision) or precision != "fp16":
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
                notes="GroqFlow hardware execution is configured for FP16",
            )
        pbs = self.spec.pbs
        assert pbs is not None
        assert self.execution is not None
        workspace = "groq-" + re.sub(r"[^A-Za-z0-9._-]", "-", variant_id)[:54]
        oracle_name = f"oracle{oracle.output_path.suffix or '.dat'}"
        worker_name = "groq_measure_worker.py"
        try:
            handshake = await self._bounded("handshake", self.execution.cached_handshake())
            await self._bounded(
                "stage candidate",
                put_bytes(self.execution, workspace, "candidate.py", module_path.read_bytes()),
            )
            await self._bounded(
                "stage oracle",
                put_bytes(self.execution, workspace, oracle_name, oracle.output_path.read_bytes()),
            )
            await self._bounded(
                "stage worker",
                put_bytes(
                    self.execution,
                    workspace,
                    worker_name,
                    Path(__file__).with_name(worker_name).read_bytes(),
                ),
            )
        except _SubmitTimeoutError as exc:
            return _submit_timeout_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                self.resource,
                exc,
            )
        request_id = uuid.uuid4().hex
        result_name = f"result-{request_id}.json"
        stdout_name = f"pbs-{request_id}.stdout"
        stderr_name = f"pbs-{request_id}.stderr"
        job_name = f"job-{request_id}.pbs"
        remote_workspace = Path(handshake.workspace_root) / workspace
        source_hash = hashlib.sha256(module_path.read_bytes()).hexdigest()
        cache_dir = remote_workspace / "groq-cache" / source_hash[:16]
        command = [
            str(pbs.python),
            worker_name,
            "--module",
            "candidate.py",
            "--oracle",
            oracle_name,
            "--output",
            result_name,
            "--iterations",
            str(config.measure.iterations),
            "--rtol",
            str(config.arena.equivalence.rtol),
            "--atol",
            str(config.arena.equivalence.atol),
            "--cache-dir",
            str(cache_dir),
            "--build-name",
            f"lassi-{variant_id}-{source_hash[:12]}",
            "--accuracy-dataset",
            config.kernel.validation_dataset,
            "--performance-dataset",
            config.measure.performance_dataset,
        ]
        script_lines = _runtime_prelude(pbs)
        script_lines.extend(
            [
                f"cd {shlex.quote(str(remote_workspace))}",
                shlex.join(command),
            ]
        )
        job_script = "\n".join(script_lines) + "\n"
        try:
            await self._bounded(
                "stage job script",
                put_bytes(self.execution, workspace, job_name, job_script.encode()),
            )
        except _SubmitTimeoutError as exc:
            return _submit_timeout_measurement(
                config,
                self.spec,
                module_path,
                candidate_id,
                variant_id,
                precision,
                compensation,
                self.resource,
                exc,
            )
        qsub = [
            str(pbs.qsub),
            "-l",
            pbs.select,
            "-l",
            f"walltime={pbs.walltime}",
            "-o",
            str(remote_workspace / stdout_name),
            "-e",
            str(remote_workspace / stderr_name),
            job_name,
        ]
        async with self.semaphore:
            try:
                submission = await self._bounded(
                    "qsub",
                    self.execution.execute(
                        ExecRequest(
                            workspace=workspace,
                            argv=qsub,
                            timeout_s=min(self.spec.timeout_s, 120.0),
                        )
                    ),
                )
            except _SubmitTimeoutError as exc:
                return _submit_timeout_measurement(
                    config,
                    self.spec,
                    module_path,
                    candidate_id,
                    variant_id,
                    precision,
                    compensation,
                    self.resource,
                    exc,
                )
            if submission.timed_out or submission.exit_code != 0:
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
                    notes=(submission.stderr or submission.stdout)[-2000:]
                    or "Groq PBS submission failed",
                )
            try:
                job_id = submission.stdout.strip().splitlines()[-1].split(".", 1)[0]
            except IndexError:
                job_id = ""
            if not job_id.isdigit():
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
                    notes=f"qsub returned no parseable job id: {submission.stdout[-1000:]}",
                )
            deadline = time.monotonic() + self.spec.timeout_s
            try:
                while time.monotonic() < deadline:
                    try:
                        payload = json.loads(
                            await fetch_bytes(self.execution, workspace, result_name)
                        )
                        break
                    except (OSError, ValueError, json.JSONDecodeError):
                        pass
                    status = await self.execution.execute(
                        ExecRequest(
                            workspace=workspace,
                            argv=[str(pbs.qsub.with_name("qstat")), "-f", job_id],
                            timeout_s=min(60.0, self.spec.timeout_s),
                        )
                    )
                    if status.timed_out:
                        continue
                    if status.exit_code != 0:
                        await asyncio.sleep(1.0)
                        try:
                            payload = json.loads(
                                await fetch_bytes(self.execution, workspace, result_name)
                            )
                        except (OSError, ValueError, json.JSONDecodeError):
                            details = (status.stderr or status.stdout)[-2000:]
                            with contextlib.suppress(OSError):
                                details = (
                                    await fetch_bytes(self.execution, workspace, stderr_name)
                                ).decode(errors="replace")[-2000:]
                            payload = {
                                "ok": False,
                                "error": f"Groq PBS job {job_id} ended without a result: {details}",
                            }
                        break
                    await asyncio.sleep(2.0)
                else:
                    await self.execution.execute(
                        ExecRequest(
                            workspace=workspace,
                            argv=[str(pbs.qsub.with_name("qdel")), job_id],
                            timeout_s=60.0,
                        )
                    )
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
                        notes=(
                            f"Groq PBS job {job_id} exceeded the backend timeout and was cancelled"
                        ),
                    )
            except asyncio.CancelledError:
                with contextlib.suppress(Exception):
                    await asyncio.shield(
                        self.execution.execute(
                            ExecRequest(
                                workspace=workspace,
                                argv=[str(pbs.qsub.with_name("qdel")), job_id],
                                timeout_s=60.0,
                            )
                        )
                    )
                raise
        return self._finalize(
            payload,
            config,
            module_path,
            candidate_id=candidate_id,
            variant_id=variant_id,
            precision=precision,
            compensation=compensation,
            mode="PBS",
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
        mode: str,
    ) -> Measurement:
        """Convert a Groq worker payload into a measurement.

        Shared by the PBS and direct compute-node modes, which differ only in
        how the worker is launched, not in what it reports.

        Args:
            payload: Decoded worker result, or any non-object on corruption.
            config: Active run configuration.
            module_path: Candidate module under measurement.
            candidate_id: Arena candidate identifier.
            variant_id: Base or compensated variant identifier.
            precision: Requested precision.
            compensation: Compensation label recorded in provenance.
            mode: Launch mode named in failure notes.

        Returns:
            Structured measurement populated from the worker payload.
        """
        if not isinstance(payload, dict):
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
                notes=f"Groq {mode} worker returned a non-object JSON payload",
            )
        if not payload.get("ok"):
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
                notes=str(payload.get("error") or f"Groq {mode} measurement failed"),
            )
        metrics = payload.get("metrics") or {}
        timing = payload.get("timing") or {}
        precision_meta = payload.get("precision") or {}
        latency = float(payload["median_s"])
        minimum = payload.get("min_s")
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
            latency_s=latency,
            min_s=latency if minimum is None else float(minimum),
            latency_scope=str(timing.get("scope", "model_forward")),
            latency_source=str(timing.get("source", "groq_sdk_benchmark")),
            latency_clock=str(timing.get("clock", "groq_runtime")),
            latency_includes_input_construction=bool(
                timing.get("includes_input_construction", False)
            ),
            latency_cuda_synchronized=False,
            max_abs_error=metrics.get("max_abs_error"),
            max_rel_error=metrics.get("max_rel_error"),
            relative_l2=metrics.get("relative_l2"),
            notes=(
                ""
                if payload.get("equivalent")
                else "measured Groq FP16 error: "
                + json.dumps(payload.get("diagnostic"), default=str)
            ),
        )
        measurement.storage_precision = str(precision_meta.get("storage", "fp16"))
        measurement.operator_precision = str(precision_meta.get("operator", "fp16"))
        measurement.accumulator_precision = str(
            precision_meta.get("accumulator", "groq-backend-defined")
        )
        measurement.output_precision = str(precision_meta.get("output", "fp16"))
        return measurement


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
            if spec.queue_dir is not None:
                result.append(GroqBackend(spec))
            else:
                resource = spec.resource or execution.default_resource
                result.append(
                    GroqBackend(
                        spec,
                        execution.backend(spec.resource),
                        resource,
                        semaphore=asyncio.Semaphore(1),
                    )
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
