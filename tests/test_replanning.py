from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from lassi_x.replanning import (
    NumericalResult,
    RepairPlan,
    ReplanningRun,
    SpecializationPlan,
    SpecializationResult,
    Variant,
)


def original(name: str, precision: str, failure: str) -> Variant:
    return Variant(
        variant_id=f"{name}_{precision}",
        source_candidate=name,
        parent_id=None,
        precision=precision,  # type: ignore[arg-type]
        repair_class="LP_ORIGINAL",
        plan_id=None,
        source=f"source of {name}",
        result=NumericalResult(failure, {"relative_l2": 0.0}),  # type: ignore[arg-type]
    )


class Worker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def plan(self, stage: str, payload: dict[str, Any], maximum: int) -> list[dict[str, Any]]:
        self.calls.append((stage, payload))
        if stage == "stage2_lp":
            return [
                {"plan_id": "1", "source_variant": "c1_fp16", "strategy": "scale"},
                {"plan_id": "2", "source_variant": "c2_bf16", "strategy": "reorder"},
            ]
        if stage == "stage2_mp":
            return [
                {
                    "plan_id": "1",
                    "source_variant": "c2_bf16",
                    "strategy": "promote reduction",
                    "promoted_operations": ["sum axis 0"],
                }
            ]
        return [
            {
                "plan_id": "1",
                "source_variant": "c1_fp16_LP1",
                "strategy": "decompose gather",
            },
            {
                "plan_id": "2",
                "source_variant": "c2_bf16_MP1",
                "strategy": "change reduction layout",
            },
        ]

    async def code_repair(self, plan: RepairPlan, source: Variant, repair_class: str) -> str:
        return f"{source.source}; {repair_class} {plan.strategy}"

    async def validate_numerical(self, source: str, precision: str) -> NumericalResult:
        failure = "finite_error" if "LP reorder" in source else "pass"
        return NumericalResult(failure, {"relative_l2": 0.1 if failure != "pass" else 0.001})  # type: ignore[arg-type]

    async def audit_precision(self, source: str, precision: str) -> tuple[str, ...]:
        return ("sum axis 0",) if "MP" in source else ()

    async def specialize(
        self, plan: SpecializationPlan, source: Variant, profile: dict[str, Any]
    ) -> SpecializationResult:
        return SpecializationResult(
            implementation=f"{source.source}; {plan.strategy}",
            compile_result="pass",
            failure_category="pass",
            repair_attempts=[],
            accuracy=NumericalResult("pass", {"relative_l2": 0.001}),
            latency_s=0.01,
        )


def test_pool_planning_and_provenance(tmp_path: Path) -> None:
    worker = Worker()
    run = ReplanningRun(
        "kernel",
        [original("c1", "fp16", "finite_error"), original("c2", "bf16", "divergent")],
        tmp_path,
        worker,
    )
    asyncio.run(run.repair(2))
    assert [stage for stage, _ in worker.calls] == ["stage2_lp", "stage2_mp"]
    assert len(worker.calls[0][1]["candidate_family"]) == 2
    assert len(worker.calls[1][1]["candidate_family"]) == 4
    assert worker.calls[1][1]["prior_plans_and_outcomes"][1]["failure_category"] == "finite_error"
    asyncio.run(run.specialize("groq", {"dtypes": ["fp16", "bf16"]}, 2))
    stage3 = worker.calls[2][1]
    assert len(stage3["candidate_family"]) == 5
    assert "c2_bf16_LP2" not in stage3["eligible_source_variants"]
    assert "compiler_errors" not in json.dumps(stage3)
    records = json.loads((tmp_path / "stage3-plans.json").read_text())
    assert records[1]["source_variant"] == "c2_bf16_MP1"
    assert records[1]["promoted_operations"] == ["sum axis 0"]
    assert records[1]["latency_s"] == 0.01


def test_rejects_promotion_in_low_precision_plan(tmp_path: Path) -> None:
    class BadWorker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            return [
                {
                    "plan_id": "1",
                    "source_variant": "c1_fp16",
                    "strategy": "upcast",
                    "promoted_operations": ["sum"],
                }
            ]

    run = ReplanningRun("kernel", [original("c1", "fp16", "finite_error")], tmp_path, BadWorker())
    with pytest.raises(ValueError, match="LP planner proposed precision promotion"):
        asyncio.run(run.repair(1))
