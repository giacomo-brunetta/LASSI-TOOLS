from __future__ import annotations

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


@dataclass(slots=True)
class Candidate:
    candidate_id: str
    model: str
    provider: str | None
    strategy: str
    module_path: Path
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
    resource: str = ""
    latency_s: float | None = None
    min_s: float | None = None
    worker_wall_s: float | None = None
    latency_scope: str = ""
    latency_source: str = ""
    latency_clock: str = ""
    latency_includes_input_construction: bool | None = None
    latency_cuda_synchronized: bool | None = None
    max_abs_error: float | None = None
    max_rel_error: float | None = None
    relative_l2: float | None = None
    invariant_error: float | None = None
    invariant_candidate: dict[str, Any] = field(default_factory=dict)
    invariant_oracle: dict[str, Any] = field(default_factory=dict)
    stochastic_samples: list[dict[str, float | int | str | None]] = field(default_factory=list)
    notes: str = ""
    source_hash: str = ""

    @property
    def y_error(self) -> float | None:
        if self.max_rel_error is not None:
            return self.max_rel_error
        if self.relative_l2 is not None:
            return self.relative_l2
        return self.invariant_error

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["y_error"] = self.y_error
        return data
