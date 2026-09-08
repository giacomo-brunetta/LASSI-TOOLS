from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectConfig(StrictModel):
    root: Path


class KernelConfig(StrictModel):
    name: str
    reference: Path
    context: list[Path] = Field(default_factory=list)
    task: str
    invariant: str | None = None
    invariant_threshold: float | None = None
    validation_dataset: str = "default"


class OracleConfig(StrictModel):
    build: list[str]
    run: list[str]
    output: Path = Path("oracle.csv")
    capture: Literal["file", "stdout", "stderr"] = "file"
    format: Literal["numeric", "polybench"] = "numeric"
    input_fixture: Path | None = None
    timeout_s: float = 600.0
    determinism_runs: int = Field(default=2, ge=1, le=10)

    @field_validator("build", "run")
    @classmethod
    def nonempty_command(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("command must not be empty")
        return value


class EquivalenceConfig(StrictModel):
    rtol: float = Field(default=1e-10, ge=0.0)
    atol: float = Field(default=1e-12, ge=0.0)
    max_mismatches: int = 20


class ArenaConfig(StrictModel):
    candidates: int = Field(default=3, ge=1, le=10)
    planner_format_retries: int = Field(default=1, ge=0, le=5)
    correction_rounds: int = Field(default=2, ge=0, le=10)
    timeout_s: float = 600.0
    equivalence: EquivalenceConfig = Field(default_factory=EquivalenceConfig)


class ModelConfig(StrictModel):
    model: str
    provider: str | None = None
    base_url: str | None = None
    api_mode: Literal["chat_completions", "responses", "anthropic_messages"] | None = None
    reasoning_effort: (
        Literal["minimal", "low", "medium", "high", "xhigh", "max", "ultra"] | None
    ) = None
    api_key_env: str | None = None
    claude_settings: Path | None = None
    max_tokens: int = Field(default=16_384, ge=256, le=131_072)
    max_iterations: int = Field(default=90, ge=1, le=500)
    turn_timeout_s: float = Field(default=600.0, gt=0.0, le=7200.0)
    turn_retries: int = Field(default=2, ge=0, le=10)
    retry_initial_s: float = Field(default=1.0, ge=0.0, le=300.0)
    retry_max_s: float = Field(default=30.0, ge=0.0, le=600.0)
    retry_jitter_s: float = Field(default=0.25, ge=0.0, le=60.0)

    @model_validator(mode="after")
    def one_credential_source(self) -> ModelConfig:
        if self.api_key_env and self.claude_settings:
            raise ValueError("set only one of api_key_env or claude_settings")
        return self


class MemoryConfig(StrictModel):
    """Long-term agent memory backed by a self-hosted Mem0 server.

    When enabled, every Hermes agent session gains the ``mem0_*`` tools and
    stores facts on the configured server, scoped by ``user_id`` plus a
    per-role agent identifier. ``api_key_env`` names the environment variable
    holding the server API key; leave it unset for servers running with
    ``AUTH_DISABLED``.
    """

    enabled: bool = False
    host: str = "http://localhost:8888"
    api_key_env: str | None = None
    user_id: str = "lassi-x"


class ModelsConfig(StrictModel):
    planner: ModelConfig
    candidates: list[ModelConfig]
    compensation: ModelConfig
    compatibility: ModelConfig | None = None

    @field_validator("candidates")
    @classmethod
    def nonempty_candidates(cls, value: list[ModelConfig]) -> list[ModelConfig]:
        if not value:
            raise ValueError("models.candidates must contain at least one entry")
        return value


class BackendCapabilities(StrictModel):
    storage: list[str] = Field(default_factory=list)
    elementwise: list[str] = Field(default_factory=list)
    matmul_accumulator: str | None = None
    explicit_fp32_tensor_ops: bool | None = None
    fp64: bool | None = None


class GroqRuntimeConfig(StrictModel):
    """Interpreter settings for a GroqRack measurement worker.

    Shared by both launch modes: the worker needs the same ``groqflow``
    environment whether PBS starts it or it runs in place on a compute node.
    """

    conda_sh: Path
    conda_env: str = "groqflow"
    python: Path
    pythonpath: list[Path] = Field(default_factory=list)


class GroqPBSConfig(GroqRuntimeConfig):
    """PBS launch settings for a GroqRack measurement resource."""

    qsub: Path = Path("/opt/pbs/bin/qsub")
    select: str = "select=1,place=excl"
    walltime: str = Field(default="01:00:00", pattern=r"^\d{1,3}:\d{2}:\d{2}$")


class NativeWorkerConfig(StrictModel):
    """Site interpreter and optional standalone worker for a native accelerator."""

    python: Path
    script: Path | None = None


class BackendConfig(StrictModel):
    type: Literal["torch", "groq", "native"]
    name: str
    device: str | None = None
    architecture: Literal["graphcore_ipu", "cerebras_wse3"] | None = None
    worker: NativeWorkerConfig | None = None
    resource: str | None = None
    queue_dir: Path | None = None
    pbs: GroqPBSConfig | None = None
    # Direct mode: the endpoint already runs on a compute node with LPUs, so
    # the worker executes in place and no batch job is involved.
    runtime: GroqRuntimeConfig | None = None
    precisions: list[Literal["fp64", "fp32", "fp16", "bf16"]]
    timeout_s: float = 600.0
    # Bounds staging and submission, not execution. A Globus Compute endpoint
    # that heartbeats but has no free worker leaves every RPC pending forever,
    # so the remote timeout on the call never gets a chance to fire.
    submit_timeout_s: float = Field(default=300.0, gt=0.0)
    healthcheck_max_age_s: float = Field(default=30.0, gt=0.0)
    stale_request_s: float = Field(default=3600.0, gt=0.0)
    capabilities: BackendCapabilities | None = None

    @model_validator(mode="after")
    def backend_requirements(self) -> BackendConfig:
        if self.type == "torch" and not self.device:
            raise ValueError("torch backend requires device")
        if self.type == "groq":
            if (self.queue_dir is None) == (self.resource is None):
                raise ValueError(
                    "groq backend requires exactly one execution mode: queue_dir, "
                    "or a resource running either PBS or direct mode"
                )
            if self.pbs is not None and self.runtime is not None:
                raise ValueError("groq backend accepts pbs or runtime, not both")
            if self.resource is not None and self.pbs is None and self.runtime is None:
                raise ValueError(
                    "groq direct mode requires runtime settings naming the "
                    "compute-node groqflow interpreter"
                )
        elif self.type == "native":
            if self.architecture is None or self.worker is None:
                raise ValueError("native backend requires architecture and worker settings")
            if self.architecture == "cerebras_wse3" and self.worker.script is None:
                raise ValueError("cerebras_wse3 backend requires a site measurement script")
            if self.device is not None:
                raise ValueError("native backend selects hardware through its site worker")
        if self.type != "groq" and (self.pbs is not None or self.runtime is not None):
            raise ValueError("pbs and runtime settings are only valid for a groq backend")
        if self.type != "native" and (self.architecture is not None or self.worker is not None):
            raise ValueError("architecture and worker settings are only valid for a native backend")
        return self


Precision = Literal["fp64", "fp32", "fp16", "bf16"]
ErrorMetric = Literal["max_rel_error", "relative_l2", "max_abs_error", "invariant_error"]


def _default_precisions() -> list[Precision]:
    return ["fp64", "fp32", "fp16", "bf16"]


def _default_strict_precisions() -> list[Precision]:
    return ["fp64", "fp32"]


class MeasureConfig(StrictModel):
    precisions: list[Precision] = Field(default_factory=_default_precisions)
    backends: list[BackendConfig]
    warmup: int = Field(default=3, ge=0)
    iterations: int = Field(default=20, ge=1)
    stochastic_seeds: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    strict_precisions: list[Precision] = Field(default_factory=_default_strict_precisions)
    serialize_torch_backends: bool = True
    evaluation_dataset: str | None = None
    evaluation_oracle: Path | None = None
    # Legacy aliases retained for existing run files; they resolve to the same
    # mandatory merged evaluation and never create a second measurement path.
    performance_dataset: str = "default"
    performance_oracle: Path | None = None
    verify_performance_output: bool = True


def _default_repair_statuses() -> list[Literal["crashed", "no_fit"]]:
    return ["crashed", "no_fit"]


class CompatibilityConfig(StrictModel):
    """Policy for repairing whole-candidate accelerator failures."""

    enabled: bool = True
    correction_rounds: int = Field(default=2, ge=0, le=10)
    repair_statuses: list[Literal["crashed", "no_fit"]] = Field(
        default_factory=_default_repair_statuses
    )


class ParetoConfig(StrictModel):
    """The scientific objective used on every latency/error frontier."""

    error_metric: ErrorMetric | None = None


class SuccessConfig(StrictModel):
    """Run-level accelerator acceptance policy.

    ``None`` requires every configured non-CPU backend. An explicit empty list
    retains exploratory behavior where any valid frontier point is sufficient.
    """

    required_backends: list[str] | None = None
    required_precisions: dict[str, list[Precision]] = Field(default_factory=dict)
    # Legacy no-op: merged device accuracy/latency verification is always required.
    require_performance_verification: bool = False

    @field_validator("required_backends")
    @classmethod
    def unique_required_backends(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("success.required_backends must be unique")
        return value


class ResourceConfig(StrictModel):
    """One compute resource that can serve execution requests."""

    endpoint_id: str | None = None
    workspace_root: Path | None = None
    labels: list[str] = Field(default_factory=list)


class ExecutionConfig(StrictModel):
    """Where agent tool calls and harness commands execute.

    ``local`` runs everything in-process against the run directory. ``academy``
    launches one ExecutionAgent per resource through an Academy manager: with
    no ``exchange_url`` the agents run on a local exchange (single machine,
    used for development and tests); with an ``exchange_url`` and per-resource
    ``endpoint_id`` values they run on remote Globus Compute endpoints.
    """

    mode: Literal["local", "academy"] = "local"
    exchange_url: str | None = None
    auth: Literal["none", "globus"] = "none"
    resources: dict[str, ResourceConfig] = Field(default_factory=dict)
    default_resource: str | None = None
    mcp_timeout_s: float = Field(default=900.0, gt=0.0)
    call_timeout_s: float = Field(default=300.0, gt=0.0)
    """Round-trip ceiling for one Academy call, on top of a command's own timeout.

    Bounds only transport and agent dispatch: an execute request adds its own
    ``timeout_s``, which the remote worker enforces. Raise this if a resource
    legitimately needs longer to acknowledge work; a response that never comes
    is what this is here to catch.
    """

    dead_after_timeouts: int = Field(default=2, ge=0)
    """Consecutive abandoned calls that take a resource out of service.

    Bounding each call is not enough when the number of calls is not bounded:
    a wedged agent otherwise costs ``call_timeout_s`` per call for the rest of
    the run. Once retired, further calls fail instantly. ``0`` disables
    retirement and restores the previous grind-forever behaviour.
    """

    heartbeat_interval_s: float = Field(default=5.0, ge=0.0)
    """Seconds between liveness pings to each remote agent; ``0`` disables them.

    The ping is a trivial Academy action that touches nothing, so this can be
    frequent. Detecting a wedged agent is otherwise gated on some real call
    hitting ``call_timeout_s``, which on 2026-08-07 meant discovering at 16:30
    that the A100 had stopped answering at 15:55.
    """

    heartbeat_misses: int = Field(default=2, ge=1)
    """Consecutive unanswered pings that pause work on a resource."""

    pause_max_s: float = Field(default=900.0, gt=0.0)
    """How long work may stay paused before the resource is retired instead.

    Long enough to restart an endpoint worker by hand, short enough that an
    unattended run does not sit paused indefinitely.
    """

    timeout_tolerant_resources: list[str] = Field(default_factory=list)
    """Resources whose abandoned calls must not discard the candidate.

    A Groq compile is legitimately minutes long, so a lost response there is
    less clearly distinguishable from slow honest work than it is elsewhere.
    Naming the resource here keeps :mod:`lassi_x.arena` from discarding a
    candidate over it. Retirement still applies -- a resource that has stopped
    answering entirely is dead whatever it was doing.
    """

    @model_validator(mode="after")
    def consistent_targets(self) -> ExecutionConfig:
        if self.default_resource is not None and self.default_resource not in self.resources:
            raise ValueError("execution.default_resource must name a configured resource")
        if self.exchange_url is not None and self.mode != "academy":
            raise ValueError("execution.exchange_url requires mode: academy")
        endpoints = [name for name, spec in self.resources.items() if spec.endpoint_id]
        if endpoints and self.exchange_url is None:
            raise ValueError(
                "resources with endpoint_id require execution.exchange_url "
                f"(offending: {', '.join(sorted(endpoints))})"
            )
        unknown_tolerant = sorted(set(self.timeout_tolerant_resources) - set(self.resources))
        if unknown_tolerant:
            raise ValueError(
                "execution.timeout_tolerant_resources must name configured resources "
                f"(offending: {', '.join(unknown_tolerant)})"
            )
        missing_roots = [
            name
            for name, spec in self.resources.items()
            if spec.endpoint_id and spec.workspace_root is None
        ]
        if missing_roots:
            raise ValueError(
                "endpoint resources require a site-local workspace_root "
                f"(offending: {', '.join(sorted(missing_roots))})"
            )
        return self


class CompensationConfig(StrictModel):
    enabled: bool = True
    correction_rounds: int = Field(default=2, ge=0, le=10)
    error_threshold: float | None = Field(default=1e-2, ge=0.0)
    error_metric: ErrorMetric = "max_rel_error"
    comparison_scope: Literal["same_candidate", "cross_candidate"] = "same_candidate"
    # Kept for configuration compatibility. Portable numerical variants are always
    # broadcast across all cells; "target" now only describes the motivating evidence.
    measurement_scope: Literal["target", "all"] = "all"
    techniques: list[str] = Field(
        default_factory=lambda: [
            "fp32-accumulate",
            "blocked-fp32",
            "pairwise",
            "kahan",
            "neumaier",
            "double-word",
            "double-word-fp32",
            "zero-center",
            "scaling",
            "equilibrate",
            "mixed-refine",
            "precision-ramp",
            "residual-carry",
            "ozaki-split",
            "stable-reformulation",
            "stochastic-round",
        ]
    )


class RunConfig(StrictModel):
    version: Literal[1]
    project: ProjectConfig
    kernel: KernelConfig
    oracle: OracleConfig
    arena: ArenaConfig = Field(default_factory=ArenaConfig)
    models: ModelsConfig
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    measure: MeasureConfig
    compatibility: CompatibilityConfig = Field(default_factory=CompatibilityConfig)
    compensation: CompensationConfig = Field(default_factory=CompensationConfig)
    pareto: ParetoConfig = Field(default_factory=ParetoConfig)
    success: SuccessConfig = Field(default_factory=SuccessConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    runs_dir: Path = Path("runs")

    @model_validator(mode="after")
    def cross_section_references_are_consistent(self) -> RunConfig:
        if len(self.models.candidates) != self.arena.candidates:
            raise ValueError(
                "models.candidates length must equal arena.candidates "
                f"({len(self.models.candidates)} != {self.arena.candidates})"
            )
        has_accelerator = any(
            spec.type in {"groq", "native"}
            or (spec.type == "torch" and str(spec.device).partition(":")[0] != "cpu")
            for spec in self.measure.backends
        )
        if has_accelerator and self.measure.warmup < 1:
            raise ValueError(
                "architectural accelerator timing requires at least one warmup invocation"
            )
        known = set(self.execution.resources) or {"local"}
        unknown = sorted(
            spec.resource
            for spec in self.measure.backends
            if spec.resource is not None and spec.resource not in known
        )
        if unknown:
            raise ValueError(
                "measure.backends name unknown execution resources: " + ", ".join(unknown)
            )
        backend_names = {spec.name for spec in self.measure.backends}
        if len(backend_names) != len(self.measure.backends):
            raise ValueError("measure.backends names must be unique")
        required = set(self.success.required_backends or [])
        unknown_required = sorted(required - backend_names)
        if unknown_required:
            raise ValueError(
                "success.required_backends name unknown measurement backends: "
                + ", ".join(unknown_required)
            )
        unknown_precision_backends = sorted(set(self.success.required_precisions) - backend_names)
        if unknown_precision_backends:
            raise ValueError(
                "success.required_precisions name unknown measurement backends: "
                + ", ".join(unknown_precision_backends)
            )
        specs_by_name = {spec.name: spec for spec in self.measure.backends}
        invalid_required_precisions = sorted(
            f"{backend}/{precision}"
            for backend, precisions in self.success.required_precisions.items()
            for precision in precisions
            if precision not in self.measure.precisions
            or precision not in specs_by_name[backend].precisions
        )
        if invalid_required_precisions:
            raise ValueError(
                "success.required_precisions contains unmeasured cells: "
                + ", ".join(invalid_required_precisions)
            )
        inactive_precision_backends = sorted(
            set(self.success.required_precisions) - set(self.required_backends)
        )
        if inactive_precision_backends:
            raise ValueError(
                "success.required_precisions must belong to required accelerator backends: "
                + ", ".join(inactive_precision_backends)
            )
        if not self.measure.verify_performance_output:
            raise ValueError(
                "merged accelerator evaluation requires measure.verify_performance_output"
            )
        if (
            self.measure.evaluation_dataset is not None
            and self.measure.performance_dataset != "default"
            and self.measure.evaluation_dataset != self.measure.performance_dataset
        ):
            raise ValueError("measure.evaluation_dataset conflicts with legacy performance_dataset")
        if (
            self.measure.evaluation_oracle is not None
            and self.measure.performance_oracle is not None
            and self.measure.evaluation_oracle != self.measure.performance_oracle
        ):
            raise ValueError("measure.evaluation_oracle conflicts with legacy performance_oracle")
        if (
            self.evaluation_dataset != self.kernel.validation_dataset
            and self.evaluation_oracle is None
        ):
            raise ValueError(
                "merged accelerator evaluation needs measure.evaluation_oracle when "
                "evaluation_dataset differs from kernel.validation_dataset"
            )
        return self

    @property
    def pareto_error_metric(self) -> ErrorMetric:
        """Return the one error metric shared by compensation and selection."""

        return self.pareto.error_metric or self.compensation.error_metric

    @property
    def evaluation_dataset(self) -> str:
        """Return the one workload used for accelerator accuracy and latency."""

        return self.measure.evaluation_dataset or self.measure.performance_dataset

    @property
    def evaluation_oracle(self) -> Path | None:
        """Return the oracle for the merged accelerator evaluation workload."""

        return self.measure.evaluation_oracle or self.measure.performance_oracle

    @property
    def required_backends(self) -> list[str]:
        """Resolve implicit accelerator requirements from configured backends."""

        if self.success.required_backends is not None:
            return self.success.required_backends
        return [
            spec.name
            for spec in self.measure.backends
            if spec.type in {"groq", "native"}
            or (spec.type == "torch" and str(spec.device).partition(":")[0] != "cpu")
        ]

    @classmethod
    def load(cls, path: Path) -> RunConfig:
        data = yaml.safe_load(path.read_text())
        cfg = cls.model_validate(data)
        base = path.resolve().parent
        if not cfg.project.root.is_absolute():
            cfg.project.root = (base / cfg.project.root).resolve()
        return cfg

    def resolve_project_path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.project.root / path
