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


class OracleConfig(StrictModel):
    build: list[str]
    run: list[str]
    output: Path = Path("oracle.csv")
    capture: Literal["file", "stdout", "stderr"] = "file"
    format: Literal["numeric", "polybench"] = "numeric"
    input_fixture: Path | None = None
    timeout_s: float = 600.0

    @field_validator("build", "run")
    @classmethod
    def nonempty_command(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("command must not be empty")
        return value


class EquivalenceConfig(StrictModel):
    rtol: float = 1e-3
    atol: float = 1e-6
    max_mismatches: int = 20


class ArenaConfig(StrictModel):
    candidates: Literal[3] = 3
    correction_rounds: int = Field(default=2, ge=0, le=10)
    timeout_s: float = 600.0
    equivalence: EquivalenceConfig = Field(default_factory=EquivalenceConfig)


class ModelConfig(StrictModel):
    model: str
    provider: str | None = None
    base_url: str | None = None
    api_mode: Literal["chat_completions", "responses", "anthropic_messages"] | None = None
    api_key_env: str | None = None
    claude_settings: Path | None = None
    max_tokens: int = Field(default=16_384, ge=256, le=131_072)
    max_iterations: int = Field(default=90, ge=1, le=500)

    @model_validator(mode="after")
    def one_credential_source(self) -> ModelConfig:
        if self.api_key_env and self.claude_settings:
            raise ValueError("set only one of api_key_env or claude_settings")
        return self


class ModelsConfig(StrictModel):
    planner: ModelConfig
    candidates: list[ModelConfig]
    compensation: ModelConfig

    @field_validator("candidates")
    @classmethod
    def exactly_three(cls, value: list[ModelConfig]) -> list[ModelConfig]:
        if len(value) != 3:
            raise ValueError("models.candidates must contain exactly three entries")
        return value


class BackendCapabilities(StrictModel):
    storage: list[str] = Field(default_factory=list)
    elementwise: list[str] = Field(default_factory=list)
    matmul_accumulator: str | None = None
    explicit_fp32_tensor_ops: bool | None = None
    fp64: bool | None = None


class BackendConfig(StrictModel):
    type: Literal["torch", "groq"]
    name: str
    device: str | None = None
    queue_dir: Path | None = None
    precisions: list[Literal["fp64", "fp32", "fp16", "bf16"]]
    timeout_s: float = 600.0
    capabilities: BackendCapabilities | None = None

    @model_validator(mode="after")
    def backend_requirements(self) -> BackendConfig:
        if self.type == "torch" and not self.device:
            raise ValueError("torch backend requires device")
        if self.type == "groq" and self.queue_dir is None:
            raise ValueError("groq backend requires queue_dir")
        return self


Precision = Literal["fp64", "fp32", "fp16", "bf16"]


def _default_precisions() -> list[Precision]:
    return ["fp64", "fp32", "fp16", "bf16"]


class MeasureConfig(StrictModel):
    precisions: list[Precision] = Field(default_factory=_default_precisions)
    backends: list[BackendConfig]
    warmup: int = Field(default=3, ge=0)
    iterations: int = Field(default=20, ge=1)
    stochastic_seeds: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])


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
    techniques: list[str] = Field(
        default_factory=lambda: [
            "fp32-accumulate",
            "pairwise",
            "kahan",
            "neumaier",
            "double-word",
            "double-word-fp32",
            "zero-center",
            "scaling",
            "mixed-refine",
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
    measure: MeasureConfig
    compensation: CompensationConfig = Field(default_factory=CompensationConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    runs_dir: Path = Path("runs")

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
