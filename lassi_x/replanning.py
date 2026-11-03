"""Pool-level Stage 2 and Stage 3 planning contract for explicit campaigns.

The campaign adapter supplies model, validation, and backend execution callbacks. This
module owns the ordering, plan validation, candidate lineage, and durable records.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    from pathlib import Path

Precision = Literal["fp32", "fp16", "bf16"]
RepairClass = Literal["LP_ORIGINAL", "LP_REPAIRED", "MP_REPAIRED", "FP32_FALLBACK"]
Failure = Literal["pass", "finite_error", "divergent", "blocked", "timeout"]


@dataclass(frozen=True)
class NumericalResult:
    failure: Failure
    metrics: dict[str, float | None]
    diagnostics: str = ""

    @property
    def valid(self) -> bool:
        return self.failure == "pass"


@dataclass(frozen=True)
class Variant:
    variant_id: str
    source_candidate: str
    parent_id: str | None
    precision: Precision
    repair_class: RepairClass
    plan_id: str | None
    source: str
    result: NumericalResult
    promoted_operations: tuple[str, ...] = ()
    operator_inventory: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.repair_class == "MP_REPAIRED" and not self.promoted_operations:
            raise ValueError("mixed precision requires named promoted operators or tensors")
        if self.repair_class == "LP_REPAIRED" and self.promoted_operations:
            raise ValueError("low-precision repair cannot promote operators")
        if self.repair_class == "FP32_FALLBACK" and self.precision != "fp32":
            raise ValueError("full FP32 fallback must be recorded at fp32")


@dataclass(frozen=True)
class RepairPlan:
    plan_id: str
    source_variant: str
    strategy: str
    promoted_operations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SpecializationPlan:
    plan_id: str
    source_variant: str
    strategy: str


@dataclass
class SpecializationResult:
    implementation: str
    compile_result: str
    failure_category: str
    repair_attempts: list[dict[str, Any]] = field(default_factory=list)
    accuracy: NumericalResult | None = None
    latency_s: float | None = None


class ReplanningWorker(Protocol):
    async def plan(self, stage: str, payload: dict[str, Any], maximum: int) -> list[dict[str, Any]]:
        """Make one global planner call and return its complete plan list."""

    async def code_repair(self, plan: RepairPlan, source: Variant, repair_class: str) -> str:
        """Implement one repair in an independent coder workspace."""

    async def validate_numerical(self, source: str, precision: Precision) -> NumericalResult:
        """Validate the complete numerical suite using the authoritative oracle."""

    async def audit_precision(self, source: str, precision: Precision) -> tuple[str, ...]:
        """Return promoted tensor/operator IDs observed in the executed graph."""

    async def specialize(
        self, plan: SpecializationPlan, source: Variant, profile: dict[str, Any]
    ) -> SpecializationResult:
        """Code, compile, validate, repair within budget, and benchmark one plan."""


def _unique_plans(rows: list[dict[str, Any]], maximum: int, sources: set[str]) -> None:
    if len(rows) > maximum:
        raise ValueError("planner exceeded the plan budget")
    ids: set[str] = set()
    strategies: set[tuple[str, str]] = set()
    for row in rows:
        plan_id = row.get("plan_id")
        source = row.get("source_variant")
        strategy = row.get("strategy")
        if not isinstance(plan_id, str) or not plan_id or plan_id in ids:
            raise ValueError("plan IDs must be unique nonempty strings")
        if source not in sources or not isinstance(strategy, str) or not strategy.strip():
            raise ValueError("plan must name an available source and a strategy")
        fingerprint = (source, " ".join(strategy.lower().split()))
        if fingerprint in strategies:
            raise ValueError("duplicate source and strategy")
        ids.add(plan_id)
        strategies.add(fingerprint)


def _variant_payload(variants: list[Variant]) -> list[dict[str, Any]]:
    return [asdict(variant) for variant in variants]


class ReplanningRun:
    """One kernel's numerical pool and per-backend specialization plans."""

    def __init__(
        self, kernel: str, originals: list[Variant], artifact_dir: Path, worker: ReplanningWorker
    ) -> None:
        if not originals or len({item.variant_id for item in originals}) != len(originals):
            raise ValueError("original pool must be nonempty with unique variant IDs")
        if any(
            item.parent_id is not None or item.repair_class != "LP_ORIGINAL" for item in originals
        ):
            raise ValueError("initial pool must contain original realizations")
        self.kernel = kernel
        self.variants = list(originals)
        self.artifact_dir = artifact_dir
        self.worker = worker
        self.stage2_records: list[dict[str, Any]] = []
        self.stage3_records: list[dict[str, Any]] = []

    def _write(self, filename: str, rows: list[dict[str, Any]]) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        target = self.artifact_dir / filename
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
        temporary.replace(target)

    async def repair(self, maximum: int, *, allow_mixed: bool = True) -> list[Variant]:
        """Plan LP first, then MP with every LP attempt and outcome as context."""

        if maximum < 0:
            raise ValueError("plan budget must be nonnegative")
        for phase in ("LP", "MP"):
            if phase == "MP" and not allow_mixed:
                break
            eligible = {
                item.variant_id
                for item in self.variants
                if item.precision in {"fp16", "bf16"}
                and not item.result.valid
                and (phase == "LP" or item.repair_class == "LP_ORIGINAL")
            }
            if not eligible or maximum == 0:
                continue
            payload = {
                "kernel": self.kernel,
                "phase": phase,
                "objective": "restore accuracy at original precision"
                if phase == "LP"
                else "selective precision rescue",
                "rules": [
                    "Use all candidates and previous outcomes to choose nonredundant plans.",
                    "Do not promote precision."
                    if phase == "LP"
                    else "Name selective promotions; full FP32 conversion is forbidden.",
                ],
                "eligible_source_variants": sorted(eligible),
                "candidate_family": _variant_payload(self.variants),
                "prior_plans_and_outcomes": self.stage2_records,
            }
            rows = await self.worker.plan(f"stage2_{phase.lower()}", payload, maximum)
            _unique_plans(rows, maximum, eligible)
            for row in rows:
                promoted = tuple(row.get("promoted_operations", ()))
                if phase == "LP" and promoted:
                    raise ValueError("LP planner proposed precision promotion")
                if phase == "MP" and (not promoted or "full_kernel" in promoted):
                    raise ValueError("MP plan requires selective named promotions")
                plan = RepairPlan(row["plan_id"], row["source_variant"], row["strategy"], promoted)
                parent = next(
                    item for item in self.variants if item.variant_id == plan.source_variant
                )
                source = await self.worker.code_repair(plan, parent, phase)
                observed_promotions = await self.worker.audit_precision(source, parent.precision)
                if set(observed_promotions) != set(promoted):
                    raise ValueError("generated repair precision differs from the plan")
                result = await self.worker.validate_numerical(source, parent.precision)
                variant = Variant(
                    variant_id=f"{parent.variant_id}_{phase}{plan.plan_id}",
                    source_candidate=parent.source_candidate,
                    parent_id=parent.variant_id,
                    precision=parent.precision,
                    repair_class="LP_REPAIRED" if phase == "LP" else "MP_REPAIRED",
                    plan_id=plan.plan_id,
                    source=source,
                    result=result,
                    promoted_operations=promoted,
                )
                if any(item.variant_id == variant.variant_id for item in self.variants):
                    raise ValueError("repair variant ID collision")
                self.variants.append(variant)
                self.stage2_records.append(
                    {
                        "kernel": self.kernel,
                        "source_candidate": parent.source_candidate,
                        "source_variant": parent.variant_id,
                        "variant_id": variant.variant_id,
                        "precision": parent.precision,
                        "plan_id": plan.plan_id,
                        "strategy": plan.strategy,
                        "repair_class": variant.repair_class,
                        "promoted_operations": promoted,
                        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                        "source": source,
                        "result": asdict(result),
                        "passed": result.valid,
                        "failure_category": result.failure,
                    }
                )
                self._write("stage2-plans.json", self.stage2_records)
        return self.variants

    async def specialize(
        self, backend: str, profile: dict[str, Any], maximum: int
    ) -> list[dict[str, Any]]:
        """Plan once across the whole family; execute each plan with its selected source."""

        if maximum < 0:
            raise ValueError("plan budget must be nonnegative")
        valid = {item.variant_id for item in self.variants if item.result.valid}
        if not valid or maximum == 0:
            return []
        payload = {
            "kernel": self.kernel,
            "backend": backend,
            "capability_profile": profile,
            "candidate_family": _variant_payload(self.variants),
            "eligible_source_variants": sorted(valid),
            "rules": [
                "Choose materially distinct backend transformations in one call.",
                "Prefer LP-valid realizations when otherwise comparable.",
                "Use only numerically valid starting points.",
                "Do not introduce precision promotion during specialization.",
                "Compiler and runtime diagnostics are available only after coding.",
            ],
        }
        rows = await self.worker.plan("stage3", payload, maximum)
        _unique_plans(rows, maximum, valid)
        for row in rows:
            plan = SpecializationPlan(row["plan_id"], row["source_variant"], row["strategy"])
            parent = next(item for item in self.variants if item.variant_id == plan.source_variant)
            outcome = await self.worker.specialize(plan, parent, profile)
            observed_promotions = await self.worker.audit_precision(
                outcome.implementation, parent.precision
            )
            if set(observed_promotions) != set(parent.promoted_operations):
                raise ValueError("specialization changed the numerical precision pattern")
            if outcome.latency_s is not None and (
                outcome.compile_result != "pass"
                or outcome.accuracy is None
                or not outcome.accuracy.valid
            ):
                raise ValueError("latency requires passing compilation and numerical validation")
            record = {
                "kernel": self.kernel,
                "backend": backend,
                "source_candidate": parent.source_candidate,
                "source_variant": parent.variant_id,
                "precision": parent.precision,
                "repair_class": parent.repair_class,
                "numerical_plan_id": parent.plan_id,
                "promoted_operations": parent.promoted_operations,
                "plan_id": plan.plan_id,
                "strategy": plan.strategy,
                "variant_id": f"{parent.variant_id}_{backend}_P{plan.plan_id}",
                "implementation": outcome.implementation,
                "implementation_sha256": hashlib.sha256(
                    outcome.implementation.encode()
                ).hexdigest(),
                "compile_result": outcome.compile_result,
                "failure_category": outcome.failure_category,
                "repair_attempts": outcome.repair_attempts,
                "accuracy": asdict(outcome.accuracy) if outcome.accuracy else None,
                "latency_s": outcome.latency_s,
            }
            self.stage3_records.append(record)
            self._write("stage3-plans.json", self.stage3_records)
        return self.stage3_records
