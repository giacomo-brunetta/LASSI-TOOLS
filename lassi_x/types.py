from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class Status(StrEnum):
    OK = "ok"
    REJECTED = "rejected"
    CRASHED = "crashed"
    DIVERGED = "diverged"
    UNSUPPORTED = "unsupported"
    NO_FIT = "no_fit"
    TIMEOUT = "timeout"


@dataclass(slots=True)
class Diagnostic:
    gate: str
    message: str
    command: list[str] = field(default_factory=list)
    exit_code: int | None = None
    stderr: str = ""
    expected_shape: list[int] | None = None
    actual_shape: list[int] | None = None
    max_abs_error: float | None = None
    max_rel_error: float | None = None
    relative_l2: float | None = None
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Diagnostic:
        return cls(**value)

    def for_agent(self) -> str:
        lines = [f"Gate: {self.gate}", f"Failure: {self.message}"]
        if self.command:
            lines.append("Command: " + " ".join(self.command))
        if self.stderr:
            lines.append("Diagnostic:\n" + self.stderr[-4000:])
        if self.expected_shape is not None:
            lines.append(
                f"Expected shape: {self.expected_shape}; actual shape: {self.actual_shape}"
            )
        if self.max_abs_error is not None:
            lines.append(
                "Numeric error: "
                f"max_abs={self.max_abs_error:.8e}, "
                f"max_rel={self.max_rel_error:.8e}, relative_l2={self.relative_l2:.8e}"
            )
        if self.mismatches:
            lines.append("First mismatches:\n" + repr(self.mismatches))
        return "\n".join(lines)


@dataclass(slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def add(self, other: Usage) -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.estimated_cost_usd += other.estimated_cost_usd

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Usage:
        return cls(**value)


@dataclass(slots=True)
class Candidate:
    candidate_id: str
    model: str
    provider: str | None
    strategy: str
    module_path: Path
    reasoning_effort: str | None = None
    parent_candidate_id: str | None = None
    target_backend: str | None = None
    target_precision: str | None = None
    status: Status = Status.CRASHED
    correction_rounds: int = 0
    diagnostics: list[Diagnostic] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    turn_outcomes: list[dict[str, str | bool | int]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["module_path"] = str(self.module_path)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Candidate:
        from pathlib import Path  # noqa: PLC0415

        data = dict(value)
        data["module_path"] = Path(data["module_path"])
        data["status"] = Status(data["status"])
        data["diagnostics"] = [Diagnostic.from_dict(item) for item in data["diagnostics"]]
        data["usage"] = Usage.from_dict(data["usage"])
        return cls(**data)


@dataclass(slots=True)
class Measurement:
    kernel: str
    candidate_id: str
    variant_id: str
    backend: str
    precision: str
    compensation: str
    status: Status
    module_path: str
    storage_precision: str
    operator_precision: str
    accumulator_precision: str
    output_precision: str
    observed_output_precision: str = ""
    precision_metadata_source: str = ""
    arithmetic_policy: str = "target_format_only"
    arithmetic_class: str = "unverified"
    observed_tensor_dtypes: list[str] = field(default_factory=list)
    wider_operations: list[dict[str, Any]] = field(default_factory=list)
    implicit_accumulator_precision: str = "unverified"
    input_contract: str = "unverified"
    input_reference_hash: str = ""
    repair_model: str = ""
    precision_verdict: str = "unverified"
    precision_audit_protocol: str = ""
    precision_audit_scope: str = ""
    precision_audit_source_hash: str = ""
    precision_violations: list[str] = field(default_factory=list)
    error_metric: str = "max_rel_error"
    evaluation_dataset: str = "default"
    accuracy_source: str = ""
    evaluation_output_checked: bool = False
    evaluation_output_finite: bool | None = None
    evaluation_output_numel: int | None = None
    evaluation_output_sha256: str = ""
    evaluation_semantic_verified: bool = False
    failure_kind: str = ""
    resource: str = ""
    latency_s: float | None = None
    min_s: float | None = None
    worker_wall_s: float | None = None
    latency_scope: str = ""
    latency_source: str = ""
    latency_clock: str = ""
    timing_protocol: str = ""
    timing_warmup_count: int | None = None
    timing_sample_count: int | None = None
    timing_invocations_per_sample: int | None = None
    timing_samples_s: list[float] = field(default_factory=list)
    timing_physical_device_count: int | None = None
    timing_input_residency: str = ""
    timing_output_residency_at_stop: str = ""
    timing_excludes: list[str] = field(default_factory=list)
    latency_includes_input_construction: bool | None = None
    latency_cuda_synchronized: bool | None = None
    max_abs_error: float | None = None
    max_rel_error: float | None = None
    relative_l2: float | None = None
    aggregate_relative_l2: float | None = None
    invariant_error: float | None = None
    invariant_candidate: dict[str, Any] = field(default_factory=dict)
    invariant_oracle: dict[str, Any] = field(default_factory=dict)
    stochastic_samples: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    source_hash: str = ""
    source_integrity_verified: bool = False
    accuracy_band: str = "unclassified"
    numerically_catastrophic: bool = False
    catastrophic_reason: str = ""

    @property
    def y_error(self) -> float | None:
        value = getattr(self, self.error_metric, None)
        return float(value) if value is not None else None

    @property
    def frontier_eligible(self) -> bool:
        """Whether this record may participate in an error/latency frontier."""

        return (
            self.status == Status.OK
            and self.precision_eligible
            and not self.numerically_catastrophic
            and self.latency_s is not None
            and self.y_error is not None
            and math.isfinite(self.latency_s)
            and math.isfinite(self.y_error)
            and self.latency_s > 0
            and self.y_error >= 0
            and self.evaluation_output_checked
            and self.evaluation_output_finite is True
            and self.evaluation_semantic_verified
            and bool(self.accuracy_source)
            and self.timing_protocol == "architectural-single-call-v1"
        )

    @property
    def precision_eligible(self) -> bool:
        """Missing evidence preserves the record, but cannot certify low-format success."""
        if self.precision == "fp64":
            return True
        if self.precision_audit_protocol == "executed-dtype-v4":
            allowed_classes = {"target_only", "control"}
            if self.arithmetic_policy == "mixed":
                allowed_classes.add("mixed_accumulation")
            if self.arithmetic_class not in allowed_classes:
                return False
        return (
            self.precision_verdict == "passed"
            and self.precision_audit_protocol
            in {"executed-dtype-v3", "executed-dtype-v4", "compiled-dtype-v1"}
            and bool(self.source_hash)
            and self.precision_audit_source_hash == self.source_hash
        )

    @property
    def stable_success(self) -> bool:
        return (
            self.status == Status.OK
            and self.precision_eligible
            and self.relative_l2 is not None
            and math.isfinite(self.relative_l2)
            and self.relative_l2 <= 0.01
            and self.evaluation_semantic_verified
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["y_error"] = self.y_error
        data["frontier_eligible"] = self.frontier_eligible
        data["precision_eligible"] = self.precision_eligible
        data["stable_success"] = self.stable_success
        return data

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Measurement:
        data = dict(value)
        data.pop("y_error", None)
        data.pop("frontier_eligible", None)
        data.pop("precision_eligible", None)
        data.pop("stable_success", None)
        data["status"] = Status(data["status"])
        return cls(**data)


@dataclass(frozen=True, slots=True)
class PruningDecision:
    candidate_id: str
    enabled: bool
    pruned: bool
    probe_backend: str | None = None
    probe_precision: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
