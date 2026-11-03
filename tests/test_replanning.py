from __future__ import annotations

import asyncio
import json
from dataclasses import replace
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


def original(name: str, precision: str, failure: str, *, fp32_failure: str = "pass") -> Variant:
    return Variant(
        variant_id=f"{name}_{precision}",
        source_candidate=name,
        parent_id=None,
        precision=precision,  # type: ignore[arg-type]
        repair_class="LP_ORIGINAL",
        plan_id=None,
        source=f"source of {name}",
        result=NumericalResult(failure, {"relative_l2": 0.0}),  # type: ignore[arg-type]
        fp64_result=NumericalResult("pass", {"relative_l2": 0.0}),
        fp32_result=NumericalResult(fp32_failure, {"relative_l2": 0.0}),  # type: ignore[arg-type]
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
        failure = (
            "finite_error"
            if precision not in {"fp64", "fp32"} and "LP reorder" in source
            else "pass"
        )
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
    assert worker.calls[1][1]["eligible_source_variants"] == ["c2_bf16"]
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


def test_precision_mismatch_is_retained_as_failed_attempt(tmp_path: Path) -> None:
    class MismatchWorker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            return [{"plan_id": "1", "source_variant": "c1_fp16", "strategy": "rescale"}]

        async def audit_precision(self, source: str, precision: str) -> tuple[str, ...]:
            return ("aten.add.Tensor",)

    run = ReplanningRun(
        "kernel", [original("c1", "fp16", "finite_error")], tmp_path, MismatchWorker()
    )
    asyncio.run(run.repair(1, allow_mixed=False))
    assert run.stage2_records[0]["failure_category"] == "blocked"
    assert "aten.add.Tensor" in run.stage2_records[0]["result"]["diagnostics"]
    assert run.variants[-1].source
    assert json.loads((tmp_path / "stage2-plans.json").read_text())[0]["passed"] is False


def test_fp32_failure_requires_separate_repair_before_lp_or_mp(tmp_path: Path) -> None:
    class FP32Worker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            self.calls.append((stage, payload))
            if stage == "stage2_fp32":
                return [{"plan_id": "1", "source_variant": "c1_fp32", "strategy": "stable formula"}]
            return []

        async def validate_numerical(self, source: str, precision: str) -> NumericalResult:
            if precision in {"fp64", "fp32"}:
                return NumericalResult("pass", {"relative_l2": 0.0})
            return NumericalResult("finite_error", {"relative_l2": 0.1})

    worker = FP32Worker()
    fp32 = original("c1", "fp32", "finite_error")
    low = original("c1", "fp16", "finite_error", fp32_failure="finite_error")
    run = ReplanningRun("kernel", [fp32, low], tmp_path, worker)
    asyncio.run(run.repair(1))
    assert [stage for stage, _ in worker.calls] == ["stage2_fp32", "stage2_lp", "stage2_mp"]
    lp_eligible = worker.calls[1][1]["eligible_source_variants"]
    assert "c1_fp16" not in lp_eligible
    assert "c1_fp32_FP321_FP16" in lp_eligible
    assert run.variants[-1].fp32_result is not None and run.variants[-1].fp32_result.valid
    assert run.stage2_records[0]["repair_class"] == "FP32_REPAIRED"
    assert len(run.stage2_records[0]["low_precision_descendants"]) == 2


def test_failed_fp32_repair_blocks_low_precision_rescue(tmp_path: Path) -> None:
    class FailedFP32Worker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            self.calls.append((stage, payload))
            return [{"plan_id": "1", "source_variant": "c1_fp32", "strategy": "still inaccurate"}]

        async def validate_numerical(self, source: str, precision: str) -> NumericalResult:
            return NumericalResult("finite_error", {"relative_l2": 0.2})

    worker = FailedFP32Worker()
    run = ReplanningRun(
        "kernel",
        [original("c1", "fp32", "finite_error"), original("c1", "fp16", "finite_error")],
        tmp_path,
        worker,
    )
    asyncio.run(run.repair(1))
    assert [stage for stage, _ in worker.calls] == ["stage2_fp32"]
    assert run.stage2_records[0]["failure_category"] == "finite_error"
    assert not any(item.repair_class == "MP_REPAIRED" for item in run.variants)


def test_stage3_excludes_low_variant_with_failed_fp32_control(tmp_path: Path) -> None:
    class NoPlanWorker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            self.calls.append((stage, payload))
            return []

    worker = NoPlanWorker()
    run = ReplanningRun(
        "kernel",
        [original("c1", "fp32", "finite_error"), original("c1", "fp16", "pass")],
        tmp_path,
        worker,
    )
    asyncio.run(run.specialize("backend", {}, 1))
    assert worker.calls == []


def test_lp_revision_is_blocked_if_its_own_fp32_control_fails(tmp_path: Path) -> None:
    class FP32RegressionWorker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            self.calls.append((stage, payload))
            if stage == "stage2_lp":
                return [{"plan_id": "1", "source_variant": "c1_fp16", "strategy": "unstable"}]
            return []

        async def validate_numerical(self, source: str, precision: str) -> NumericalResult:
            if precision == "fp32":
                return NumericalResult("finite_error", {"relative_l2": 0.3})
            return NumericalResult("pass", {"relative_l2": 0.0})

    worker = FP32RegressionWorker()
    run = ReplanningRun("kernel", [original("c1", "fp16", "finite_error")], tmp_path, worker)
    asyncio.run(run.repair(1, allow_mixed=False))
    assert run.stage2_records[0]["failure_category"] == "blocked"
    assert run.stage2_records[0]["fp32_result"]["failure"] == "finite_error"
    assert run.variants[-1].fp32_result is not None
    assert not run.variants[-1].fp32_result.valid


@pytest.mark.parametrize("phase", ["FP32", "LP", "MP"])
@pytest.mark.parametrize("raises", [False, True])
def test_changed_source_requires_fresh_fp64(tmp_path: Path, phase: str, raises: bool) -> None:
    class GateWorker(Worker):
        def __init__(self) -> None:
            super().__init__()
            self.validations: list[tuple[str, str]] = []

        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            if stage != f"stage2_{phase.lower()}":
                return []
            return [
                {
                    "plan_id": "1",
                    "source_variant": payload["eligible_source_variants"][0],
                    "strategy": "changed",
                    "promoted_operations": ["sum axis 0"] if phase == "MP" else [],
                }
            ]

        async def validate_numerical(self, source: str, precision: str) -> NumericalResult:
            self.validations.append((source, precision))
            assert precision == "fp64", "failed FP64 must stop downstream validation"
            if raises:
                raise RuntimeError("validator unavailable")
            return NumericalResult("finite_error", {"relative_l2": 1.0})

    worker = GateWorker()
    precision = "fp32" if phase == "FP32" else "fp16"
    run = ReplanningRun("kernel", [original("c1", precision, "finite_error")], tmp_path, worker)
    asyncio.run(run.repair(1))
    assert len(worker.validations) == 1
    assert worker.validations[0][0] != run.variants[0].source
    assert not run.variants[-1].result.valid
    control = run.variants[-1].fp64_result
    if raises:
        assert control is None
    else:
        assert control is not None and not control.valid
    record = json.loads((tmp_path / "stage2-plans.json").read_text())[0]
    assert record["passed"] is False
    assert (
        record["fp64_result"] is None
        if raises
        else record["fp64_result"]["failure"] == "finite_error"
    )


def test_missing_fp64_cannot_enter_repair_or_specialization(tmp_path: Path) -> None:
    worker = Worker()
    for failure in ("pass", "finite_error"):
        run = ReplanningRun(
            "kernel", [replace(original("c1", "fp16", failure), fp64_result=None)], tmp_path, worker
        )
        asyncio.run(run.repair(1))
        assert asyncio.run(run.specialize("backend", {}, 1)) == []
    assert worker.calls == []


@pytest.mark.parametrize("raises", [False, True])
def test_specialization_cannot_accept_inherited_fp64(tmp_path: Path, raises: bool) -> None:
    class SpecializationWorker(Worker):
        async def plan(
            self, stage: str, payload: dict[str, Any], maximum: int
        ) -> list[dict[str, Any]]:
            return [{"plan_id": "1", "source_variant": "c1_fp16", "strategy": "changed"}]

        async def validate_numerical(self, source: str, precision: str) -> NumericalResult:
            assert source == "source of c1; changed"
            assert precision == "fp64"
            if raises:
                raise RuntimeError("validator unavailable")
            return NumericalResult("finite_error", {"relative_l2": 1.0})

    run = ReplanningRun(
        "kernel", [original("c1", "fp16", "pass")], tmp_path, SpecializationWorker()
    )
    records = asyncio.run(run.specialize("backend", {}, 1))
    assert records[0]["implementation"] == "source of c1; changed"
    assert records[0]["compile_result"] == "blocked"
    assert records[0]["latency_s"] is None
    assert (
        records[0]["fp64_result"] is None
        if raises
        else records[0]["fp64_result"]["failure"] == "finite_error"
    )
