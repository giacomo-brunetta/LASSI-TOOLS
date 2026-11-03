"""Run one frozen Luna candidate family through pool-level replanning.

Stage 1 is produced separately with ``lassi-x run ... --until cpu-verified``.
Pass that exact run path; this adapter never searches for a recent run.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import torch

from lassi_x.candidate_runner import PRECISIONS
from lassi_x.config import RunConfig
from lassi_x.hermes import HermesSession
from lassi_x.replanning import (
    NumericalResult,
    Precision,
    RepairPlan,
    ReplanningRun,
    SpecializationPlan,
    SpecializationResult,
    ValidationPrecision,
    Variant,
)

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = Path(__file__).resolve().parent
OUTPUT = REPO / "runs/replanning-luna-correlation-mini-20261102"
ORACLE = OUTPUT / "oracle-preflight/oracle/oracle.csv"
INPUT_CONTRACT = OUTPUT / "oracle-preflight/oracle/input-contract/inputs.npz"
CHECKS = EXAMPLE / "checks.py"
ACCURACY_THRESHOLD = 0.001


def _json_response(raw: str) -> list[dict[str, Any]]:
    value = raw.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value)
    parsed = json.loads(value)
    if not isinstance(parsed, list) or any(not isinstance(item, dict) for item in parsed):
        raise ValueError("planner did not return a JSON array of objects")
    return parsed


def _code_response(raw: str) -> str:
    match = re.search(r"```(?:python)?\s*\n([\s\S]*?)\n```", raw)
    source = match.group(1) if match else raw.strip()
    ast.parse(source)
    if "def build_inputs" not in source or "def make_model" not in source:
        raise ValueError("coder response omitted the candidate module interface")
    return source.rstrip() + "\n"


class LunaWorker:
    def __init__(self, config: RunConfig, artifacts: Path, target_device: str) -> None:
        self.config = config
        self.artifacts = artifacts
        self.target_device = target_device
        self.model_calls = 0
        self.artifacts.mkdir(parents=True, exist_ok=True)

    async def _model(self, role: str, prompt: str, *, system: str) -> str:
        if self.model_calls >= 15:
            raise RuntimeError("Luna session budget exhausted")
        self.model_calls += 1
        workspace = self.artifacts / "model" / f"{self.model_calls:02d}-{role}"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "prompt.txt").write_text(prompt)
        if "stage2_fp32" in role or "coder-FP32" in role:
            skill_role = "replanning-fp32-" + role
        elif "stage2_lp" in role or "coder-LP" in role:
            skill_role = "replanning-lp-" + role
        elif "stage2_mp" in role or "coder-MP" in role:
            skill_role = "replanning-mp-" + role
        else:
            skill_role = "replanning-specialization-" + role
        async with HermesSession(
            self.config.models.planner,
            cwd=workspace,
            system_prompt=system,
            toolsets=["skills"],
            role=skill_role,
        ) as session:
            turn = await session.send(prompt)
        (workspace / "response.txt").write_text(turn.text)
        (workspace / "usage.json").write_text(
            json.dumps(
                {
                    "completed": turn.completed,
                    "exit_reason": turn.exit_reason,
                    "input_tokens": turn.usage.input_tokens,
                    "output_tokens": turn.usage.output_tokens,
                    "estimated_cost_usd": turn.usage.estimated_cost_usd,
                },
                indent=2,
            )
            + "\n"
        )
        if not turn.completed:
            raise RuntimeError(f"Luna did not complete {role}: {turn.exit_reason}")
        return turn.text

    async def plan(self, stage: str, payload: dict[str, Any], maximum: int) -> list[dict[str, Any]]:
        schema = (
            '[{"plan_id":"1","source_variant":"...","strategy":"...",'
            '"promoted_operations":["aten._to_copy.default","aten.sum.dim_IntList"]}]'
            if stage == "stage2_mp"
            else '[{"plan_id":"1","source_variant":"...","strategy":"..."}]'
        )
        stage_rule = {
            "stage2_fp32": "FP32 repair must preserve FP32 arithmetic; no FP64 tensor upcast. ",
            "stage2_lp": "LP may not promote precision. ",
            "stage2_mp": (
                "MP must name each exact ATen operation that will see a wider tensor, "
                "including cast operations; full-kernel upcasting is forbidden. "
            ),
            "stage3": "Stage 3 must preserve the selected precision pattern. ",
        }[stage]
        prompt = (
            f"Stage: {stage}. Return zero to {maximum} materially distinct plans "
            "in one JSON array and no other text. Use exactly this shape: "
            f"{schema}\n"
            "Every source_variant must be an eligible ID. Do not select blocked or failed "
            "variants for Stage 3. "
            + stage_rule
            + "Do not invent compiler failures. Return [] when no "
            "nonredundant feasible strategy exists.\n\n" + json.dumps(payload, indent=2)
        )
        raw = await self._model(
            f"planner-{stage}",
            prompt,
            system="You are a scientific numerical and accelerator planner. Return JSON only.",
        )
        return _json_response(raw)

    async def _code(self, role: str, source: Variant, strategy: str, precision: str) -> str:
        c_reference = (
            REPO / "benchmarks/polybench/datamining/correlation/correlation.c"
        ).read_text()
        prompt = (
            "Return the COMPLETE candidate.py module as one Python code fence. "
            "Implement the assigned strategy faithfully. Preserve build_inputs, "
            "make_model, and FP64 C semantics. Do not change the reference or validation. "
            "Do not hard-code outputs or reconstruct supplied inputs. "
            f"Requested low precision: {precision}.\nStrategy: {strategy}\n\n"
            f"Current module:\n```python\n{source.source}\n```\n\n"
            f"Authoritative C source:\n```c\n{c_reference}\n```"
        )
        raw = await self._model(
            role,
            prompt,
            system="You are a coder implementing exactly one assigned plan. Output code only.",
        )
        return _code_response(raw)

    async def code_repair(self, plan: RepairPlan, source: Variant, repair_class: str) -> str:
        strategy = f"{repair_class}: {plan.strategy}"
        if repair_class == "LP":
            strategy += " No explicit FP32/FP64 tensor arithmetic, including helper code."
        elif repair_class == "FP32":
            strategy += (
                " Repair FP32 accuracy through a new algorithmic formulation. "
                "Do not use FP64 tensor arithmetic or a precision fallback."
            )
        else:
            strategy += (
                " Promote only the named ATen operations and necessary casts: "
                + ", ".join(plan.promoted_operations)
                + ". Retain low-precision storage and output."
            )
        coded = await self._code(
            f"coder-{repair_class}-{plan.plan_id}", source, strategy, source.precision
        )
        target = (
            self.artifacts / "stage2-code" / f"{source.variant_id}_{repair_class}{plan.plan_id}.py"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(coded)
        return coded

    def _check(self, args: list[str], *, timeout: float = 120) -> dict[str, Any]:
        result = subprocess.run(
            [sys.executable, *args],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "0"},
        )
        try:
            record = cast("dict[str, Any]", json.loads(result.stdout.strip().splitlines()[-1]))
        except (IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"check produced no JSON: {result.stderr[-600:]}") from exc
        return record

    def _source_path(self, source: str) -> Path:
        digest = hashlib.sha256(source.encode()).hexdigest()
        path = self.artifacts / "evaluated-sources" / f"{digest}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        return path

    def _measure(self, source: str, precision: str, *, mixed: bool = False) -> dict[str, Any]:
        module = self._source_path(source)
        argv = [
            "--module",
            str(module),
            "--oracle",
            str(ORACLE),
            "--device",
            "cpu",
            "--precision",
            precision,
            "--dataset",
            "mini",
            "--warmup",
            "1",
            "--iterations",
            "2",
            "--input-contract",
            str(INPUT_CONTRACT),
            "--rtol",
            "1e-10" if precision == "fp64" else "0.01",
            "--atol",
            "1e-12" if precision == "fp64" else "1e-5",
        ]
        if precision == "fp64":
            argv.append("--require-equivalence")
        command = ["-m", "lassi_x.measure_worker", *argv]
        if mixed:
            command = [
                "-c",
                "import sys, lassi_x.measure_worker as w; "
                "w._PRECISION_AUDIT_ACTIVE=True; "
                "sys.argv=['lassi_x.measure_worker',*sys.argv[1:]]; "
                "raise SystemExit(w.main())",
                *argv,
            ]
        return self._check(command)

    @staticmethod
    def _numerical(record: dict[str, Any]) -> NumericalResult:
        if not record.get("ok"):
            phase = str(record.get("phase") or "execution")
            category = "timeout" if "timeout" in phase else "blocked"
            return NumericalResult(category, {}, str(record.get("error") or phase)[:800])  # type: ignore[arg-type]
        metrics = record.get("metrics") or {}
        error = metrics.get("relative_l2")
        finite = bool(record.get("evaluation_output", {}).get("finite"))
        if not finite:
            failure = "divergent"
        elif error is None:
            failure = "blocked"
        elif error <= ACCURACY_THRESHOLD:
            failure = "pass"
        else:
            failure = "finite_error"
        diagnostic = record.get("diagnostic") or {}
        return NumericalResult(
            failure,  # type: ignore[arg-type]
            {key: float(value) if value is not None else None for key, value in metrics.items()},
            str(diagnostic.get("message") or "")[:800],
        )

    async def validate_numerical(
        self, source: str, precision: ValidationPrecision
    ) -> NumericalResult:
        control = self._measure(source, "fp64")
        if not control.get("ok") or not control.get("equivalent"):
            return NumericalResult("blocked", {}, "FP64 semantic or input-parity gate failed")
        if precision == "fp64":
            return self._numerical(control)
        audit = await self._audit(source, precision)
        return self._numerical(
            self._measure(source, precision, mixed=bool(audit["promoted_operations"]))
        )

    async def _audit(self, source: str, precision: Precision) -> dict[str, Any]:
        record = self._check(
            [
                str(CHECKS),
                "audit",
                "--module",
                str(self._source_path(source)),
                "--precision",
                precision,
                "--device",
                "cpu",
            ]
        )
        digest = hashlib.sha256(source.encode()).hexdigest()
        path = self.artifacts / "precision-audits" / f"{digest}-{precision}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n")
        if not record.get("ok") or not record.get("complete"):
            raise RuntimeError(f"precision audit incomplete: {record.get('error')}")
        return record

    async def audit_precision(self, source: str, precision: Precision) -> tuple[str, ...]:
        record = await self._audit(source, precision)
        extras = []
        if record.get("host_scalar"):
            extras.append("host_scalar")
        if record.get("wrong_output_dtypes"):
            extras.append("wrong_output_dtype")
        return tuple([*record["promoted_operations"], *extras])

    async def specialize(
        self, plan: SpecializationPlan, source: Variant, profile: dict[str, Any]
    ) -> SpecializationResult:
        strategy = (
            f"Backend {self.target_device} profile: {json.dumps(profile)}. "
            f"Implement only this plan: {plan.strategy}. Do not add precision promotion."
        )
        coded = await self._code(f"coder-stage3-{plan.plan_id}", source, strategy, source.precision)
        attempts: list[dict[str, Any]] = []
        for attempt in range(2):
            target = (
                self.artifacts / "stage3-code" / f"{source.variant_id}_{plan.plan_id}_{attempt}.py"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(coded)
            observed = await self.audit_precision(coded, source.precision)
            if set(observed) != set(source.promoted_operations):
                return SpecializationResult(coded, "blocked", "precision_pattern_changed", attempts)
            record = self._check(
                [
                    str(CHECKS),
                    "target",
                    "--module",
                    str(target),
                    "--precision",
                    source.precision,
                    "--device",
                    self.target_device,
                    "--oracle",
                    str(ORACLE),
                    "--input-contract",
                    str(INPUT_CONTRACT),
                ]
            )
            attempts.append({"attempt": attempt + 1, "result": record})
            if record.get("ok"):
                accuracy = record["accuracy"]
                return SpecializationResult(
                    coded,
                    record["compile_result"],
                    accuracy["failure"],
                    attempts,
                    NumericalResult(**accuracy),
                    record.get("latency_s"),
                )
            if attempt == 0:
                coded = await self._code(
                    f"repair-stage3-{plan.plan_id}",
                    Variant(
                        variant_id=source.variant_id,
                        source_candidate=source.source_candidate,
                        parent_id=source.parent_id,
                        precision=source.precision,
                        repair_class=source.repair_class,
                        plan_id=source.plan_id,
                        source=coded,
                        result=source.result,
                        promoted_operations=source.promoted_operations,
                    ),
                    "Repair this compiler/runtime failure without changing the plan: "
                    + str(record.get("error")),
                    source.precision,
                )
        return SpecializationResult(coded, "blocked", "compiler_or_runtime", attempts)


def _profile(device: str) -> dict[str, Any]:
    dtypes = []
    for precision in ("fp32", "fp16", "bf16"):
        try:
            tensor = torch.ones(2, device=device, dtype=PRECISIONS[precision])
            _ = tensor + tensor
            dtypes.append(precision)
        except Exception:  # noqa: BLE001  # capability probe is explicitly recorded
            continue
    return {
        "backend": "torchscript-mps-demo-v1",
        "device": device,
        "supported_dtypes_probed": dtypes,
        "supported_operators": "unknown until whole-graph trace and execution",
        "shape_restrictions": "fixed MINI shape in this example",
        "graph_restrictions": "TorchScript tracing; data-dependent branches may not trace",
        "limitations": "MPS may lower or accumulate at different internal precision",
    }


async def main(stage1_run: Path, device: str, *, baseline_only: bool = False) -> None:
    config = RunConfig.load(EXAMPLE / "stage1.yaml")
    report = json.loads((stage1_run / "run.json").read_text())
    if report.get("kernel") != config.kernel.name:
        raise ValueError("Stage 1 run has a different kernel")
    if not ORACLE.is_file() or not INPUT_CONTRACT.is_file():
        raise FileNotFoundError("frozen C oracle or input contract missing")
    worker = LunaWorker(config, OUTPUT / "replanning", device)
    originals: list[Variant] = []
    baseline: list[dict[str, Any]] = []
    candidates = {item["candidate_id"]: item for item in report.get("candidates", [])}
    for candidate_id in ("c1", "c2", "c3"):
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise ValueError(f"Stage 1 missing planned candidate {candidate_id}")
        path = Path(candidate["module_path"])
        source = path.read_text() if path.is_file() else ""
        control = worker._measure(source, "fp64") if source else {"ok": False, "error": "no source"}
        control_metrics = cast("dict[str, Any]", control.get("metrics") or {})
        fp64 = NumericalResult(
            "pass" if control.get("ok") and control.get("equivalent") else "blocked",
            {
                str(key): float(value) if value is not None else None
                for key, value in control_metrics.items()
            },
            str(control.get("error") or "")[:800],
        )
        for precision in ("fp32", "fp16", "bf16"):
            measurement = (
                worker._measure(source, precision)
                if fp64.valid
                else {"ok": False, "error": "FP64 gate failed"}
            )
            numerical = worker._numerical(measurement)
            if precision in {"fp16", "bf16"} and numerical.valid:
                audit = await worker._audit(source, precision)
                if (
                    audit["promoted_operations"]
                    or audit["host_scalar"]
                    or audit["wrong_output_dtypes"]
                ):
                    numerical = NumericalResult(
                        "blocked", numerical.metrics, "explicit precision audit failed"
                    )
            originals.append(
                Variant(
                    variant_id=f"{candidate_id}_{precision.upper()}",
                    source_candidate=candidate_id,
                    parent_id=None,
                    precision=precision,
                    repair_class="LP_ORIGINAL",
                    plan_id=None,
                    source=source,
                    result=numerical,
                    fp64_result=fp64,
                )
            )
            baseline.append(
                {
                    "candidate": candidate_id,
                    "precision": precision,
                    "fp64": asdict(fp64),
                    "result": asdict(numerical),
                    "measurement": measurement,
                    "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                }
            )
    (OUTPUT / "baseline.json").write_text(json.dumps(baseline, indent=2) + "\n")
    if baseline_only:
        print(
            json.dumps(
                {
                    "baseline_cells": len(baseline),
                    "failure_categories": [
                        (item["candidate"], item["precision"], item["result"]["failure"])
                        for item in baseline
                    ],
                },
                indent=2,
            )
        )
        return
    run = ReplanningRun(config.kernel.name, originals, OUTPUT / "replanning", worker)
    await run.repair(2)
    profile = _profile(device)
    (OUTPUT / "backend-profile.json").write_text(json.dumps(profile, indent=2) + "\n")
    await run.specialize(device, profile, 2)
    summary = {
        "stage1_run": str(stage1_run),
        "kernel": config.kernel.name,
        "planned_baseline_cells": 9,
        "baseline_passed": sum(item["result"]["failure"] == "pass" for item in baseline),
        "stage2_plans": len(run.stage2_records),
        "stage2_passed": sum(item["passed"] for item in run.stage2_records),
        "stage3_plans": len(run.stage3_records),
        "stage3_accurate": sum(
            item["accuracy"] is not None and item["accuracy"]["failure"] == "pass"
            for item in run.stage3_records
        ),
        "luna_sessions_after_preflight": worker.model_calls,
        "precision_claim": "observed explicit eager operations only; compiled dtype unverified",
        "timing_claim": "host-synchronized MPS call, not architectural device timing",
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


async def revalidate_stage3(device: str) -> None:
    """Recheck saved implementations after a trusted checker fix, without model calls."""

    config = RunConfig.load(EXAMPLE / "stage1.yaml")
    worker = LunaWorker(config, OUTPUT / "replanning", device)
    original = json.loads((OUTPUT / "replanning/stage3-plans.json").read_text())
    recovered: list[dict[str, Any]] = []
    for row in original:
        source = str(row["implementation"])
        digest = hashlib.sha256(source.encode()).hexdigest()
        if digest != row["implementation_sha256"]:
            raise ValueError(f"saved Stage 3 source hash mismatch for plan {row['plan_id']}")
        path = OUTPUT / "replanning/revalidation-sources" / f"{row['variant_id']}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        observed = await worker.audit_precision(source, row["precision"])
        target_audit = worker._check(
            [
                str(CHECKS),
                "audit",
                "--module",
                str(path),
                "--precision",
                row["precision"],
                "--device",
                device,
            ]
        )
        if set(observed) != set(row["promoted_operations"]):
            result: dict[str, Any] = {
                "ok": False,
                "error": "saved implementation changed selected precision pattern",
                "observed_promotions": observed,
            }
        else:
            result = worker._check(
                [
                    str(CHECKS),
                    "target",
                    "--module",
                    str(path),
                    "--precision",
                    row["precision"],
                    "--device",
                    device,
                    "--oracle",
                    str(ORACLE),
                    "--input-contract",
                    str(INPUT_CONTRACT),
                ]
            )
        recovered.append(
            {
                "plan_id": row["plan_id"],
                "source_variant": row["source_variant"],
                "implementation_sha256": digest,
                "original_failure_category": row["failure_category"],
                "checker_protocol": "mps-host-transfer-before-fp64-v2",
                "model_calls": 0,
                "target_eager_precision_audit": target_audit,
                "result": result,
            }
        )
    output = OUTPUT / "replanning/stage3-revalidated-v2.json"
    output.write_text(json.dumps(recovered, indent=2) + "\n")
    print(
        json.dumps(
            {
                "revalidated": len(recovered),
                "accurate": sum(
                    item["result"].get("accuracy", {}).get("failure") == "pass"
                    for item in recovered
                ),
                "model_calls": worker.model_calls,
                "artifact": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1-run", type=Path)
    parser.add_argument("--device", default="mps")
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--revalidate-stage3", action="store_true")
    arguments = parser.parse_args()
    if arguments.revalidate_stage3:
        asyncio.run(revalidate_stage3(arguments.device))
    else:
        if arguments.stage1_run is None:
            parser.error("--stage1-run is required unless --revalidate-stage3 is set")
        asyncio.run(
            main(
                arguments.stage1_run.resolve(),
                arguments.device,
                baseline_only=arguments.baseline_only,
            )
        )
