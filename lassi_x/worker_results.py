"""Validate measurement evidence before it can influence acceptance."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class EvidenceModel(BaseModel):
    # SDKs may attach additional diagnostics; known evidence fields stay strict.
    model_config = ConfigDict(extra="allow", strict=True, allow_inf_nan=False)


class TimingEvidence(EvidenceModel):
    protocol: str = ""
    scope: str = ""
    source: str = ""
    clock: str = ""
    includes_input_construction: bool = False
    cuda_synchronized: bool = False
    warmup_count: int | None = Field(default=None, ge=0)
    sample_count: int | None = Field(default=None, ge=0)
    invocations_per_sample: int | None = Field(default=None, ge=1)
    physical_device_count: int | None = Field(default=None, ge=1)
    samples_s: list[Annotated[float, Field(gt=0)]] = Field(default_factory=list)
    input_residency: str = ""
    output_residency_at_stop: str = ""
    excludes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def matching_sample_count(self) -> TimingEvidence:
        if self.sample_count is not None and self.sample_count != len(self.samples_s):
            raise ValueError("timing sample_count does not match samples_s")
        return self


class EvaluationEvidence(EvidenceModel):
    checked: bool = False
    finite: bool | None = None
    semantic_verified: bool = False
    numel: int | None = Field(default=None, ge=0)
    sha256: str = ""
    accuracy_source: str = ""


ErrorValue = Annotated[float, Field(allow_inf_nan=True)]


class ErrorMetrics(EvidenceModel):
    # Nonfinite numerical error is legitimate divergence evidence, not a latency.
    max_abs_error: ErrorValue | None = None
    max_rel_error: ErrorValue | None = None
    relative_l2: ErrorValue | None = None
    aggregate_relative_l2: ErrorValue | None = None


class WorkerResult(EvidenceModel):
    schema_version: Literal[1] = 1
    ok: bool
    valid: bool | None = None
    equivalent: bool | None = None
    median_s: float | None = Field(default=None, gt=0)
    min_s: float | None = Field(default=None, gt=0)
    timing: TimingEvidence = Field(default_factory=TimingEvidence)
    evaluation_output: EvaluationEvidence = Field(default_factory=EvaluationEvidence)
    metrics: ErrorMetrics = Field(default_factory=ErrorMetrics)
    precision: dict[str, str] = Field(default_factory=dict)
    invariant_error: ErrorValue | None = None
    source_hash: str = ""
    phase: str = ""
    error: str = ""

    @model_validator(mode="after")
    def successful_timing(self) -> WorkerResult:
        if self.ok and (self.median_s is None or self.min_s is None):
            raise ValueError("successful worker result requires median_s and min_s")
        return self


class QueueResult(EvidenceModel):
    schema_version: Literal[1] = 1
    status: Literal["ok", "rejected", "crashed", "diverged", "unsupported", "no_fit", "timeout"]
    timing: TimingEvidence = Field(default_factory=TimingEvidence)
    latency_s: float | None = Field(default=None, gt=0)
    min_s: float | None = Field(default=None, gt=0)
    accuracy_checked: bool = False
    accuracy_finite: bool | None = None
    accuracy_oracle_compared: bool = False
    accuracy_numel: int | None = Field(default=None, ge=0)
    max_abs_error: ErrorValue | None = None
    max_rel_error: ErrorValue | None = None
    relative_l2: ErrorValue | None = None
    aggregate_relative_l2: ErrorValue | None = None
    invariant_error: ErrorValue | None = None

    @model_validator(mode="after")
    def successful_timing(self) -> QueueResult:
        if self.status == "ok" and (self.latency_s is None or self.min_s is None):
            raise ValueError("successful queue result requires latency_s and min_s")
        return self


def validate_worker_result(payload: Any, *, queued: bool = False) -> dict[str, Any]:
    """Turn malformed records into explicit protocol failures, never successes."""
    try:
        model = QueueResult if queued else WorkerResult
        return model.model_validate(payload).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return {
            "ok": False,
            "status": "crashed",
            "phase": "worker_protocol",
            "error": f"invalid measurement evidence: {exc}",
            "notes": f"invalid measurement evidence: {exc}",
        }
