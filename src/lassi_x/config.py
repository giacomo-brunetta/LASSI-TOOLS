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


class ModelsConfig(StrictModel):
    planner: ModelConfig
    candidates: list[ModelConfig]
    compensation: ModelConfig

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


class BackendConfig(StrictModel):
    type: Literal["torch", "groq"]
    name: str
    device: str | None = None
    queue_dir: Path | None = None
    precisions: list[Literal["fp64", "fp32", "fp16", "bf16"]]
    timeout_s: float = 600.0
    healthcheck_max_age_s: float = Field(default=30.0, gt=0.0)
    stale_request_s: float = Field(default=3600.0, gt=0.0)
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


class CompensationConfig(StrictModel):
    enabled: bool = True
    correction_rounds: int = Field(default=2, ge=0, le=10)
    error_threshold: float | None = Field(default=1e-2, ge=0.0)
    error_metric: Literal["max_rel_error", "relative_l2", "max_abs_error", "invariant_error"] = (
        "max_rel_error"
    )
    comparison_scope: Literal["same_candidate", "cross_candidate"] = "same_candidate"
    measurement_scope: Literal["target", "all"] = "target"
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
    runs_dir: Path = Path("runs")

    @model_validator(mode="after")
    def candidate_model_count_matches_arena(self) -> RunConfig:
        if len(self.models.candidates) != self.arena.candidates:
            raise ValueError(
                "models.candidates length must equal arena.candidates "
                f"({len(self.models.candidates)} != {self.arena.candidates})"
            )
        return self

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
