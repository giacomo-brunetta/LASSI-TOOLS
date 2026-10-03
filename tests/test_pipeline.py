from __future__ import annotations

import asyncio
import json
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import yaml

import lassi_x.pipeline as pipeline
import lassi_x.run_record as run_record
from lassi_x.cli import build_parser
from lassi_x.compensation import CompensationVariant
from lassi_x.config import ExecutionConfig, RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.qualification import QualificationResult
from lassi_x.scheduler import PipelineScheduler
from lassi_x.types import Candidate, Measurement, Status
from lassi_x.validation import OracleResult

from .test_config import minimal_config
from .test_validation import GOOD_MODULE

if TYPE_CHECKING:
    from pathlib import Path


def measured(
    module: Path,
    *,
    variant_id: str,
    compensation: str,
    error: float,
) -> Measurement:
    return Measurement(
        kernel="tiny",
        candidate_id="c1",
        variant_id=variant_id,
        backend="cpu",
        precision="fp16",
        compensation=compensation,
        status=Status.OK,
        module_path=str(module),
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        latency_s=1.0,
        max_rel_error=error,
        relative_l2=error,
        evaluation_output_checked=True,
        evaluation_output_finite=True,
        evaluation_semantic_verified=True,
        accuracy_source="timed_device_workload",
        timing_protocol="architectural-single-call-v1",
        latency_scope="device_resident_graph",
    )


def test_pipeline_compensates_single_high_error_survivor(tmp_path: Path, monkeypatch: Any) -> None:
    data = minimal_config(tmp_path)
    data["runs_dir"] = str(tmp_path / "runs")
    data["compensation"] = {"error_threshold": 0.01, "measurement_scope": "all"}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    base_point = measured(module, variant_id="c1-base", compensation="none", error=0.05)
    captured_specs: list[tuple[str, str, Path, str, str, str]] = []

    async def fake_oracle(config: object, run_dir: object) -> OracleResult:
        del config, run_dir
        return OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def fake_plan(*_: object) -> tuple[list[str], dict[str, object]]:
        return ["direct"], {"text": "plan", "usage": {}}

    async def fake_generate(*_: object) -> Candidate:
        return candidate

    async def fake_measure_base(*_: object, **kwargs: object) -> list[Measurement]:
        callback = kwargs.get("on_result")
        if callable(callback):
            callback(base_point)
        return [base_point]

    async def fake_compensation(
        config: object,
        oracle: object,
        run_dir: Path,
        execution: object,
        base: Candidate,
        weak_points: list[Measurement],
        backends: list[object],
        *,
        target_backends: dict[str, object] | None = None,
        guard_points: list[Measurement] | None = None,
    ) -> CompensationVariant:
        del config, oracle, execution, backends, target_backends
        assert base is candidate
        assert weak_points == [base_point]
        assert guard_points == []
        target = run_dir / "variant.py"
        target.write_text(GOOD_MODULE.replace("return x\n", "return x + 0\n"))
        return CompensationVariant(
            "c1",
            "n-c1-fp16",
            "portable",
            "fp16",
            "kahan",
            target,
            status=Status.OK,
            target_backends=["cpu"],
        )

    async def fake_measure_compensation(
        config: object,
        oracle: object,
        specs: list[tuple[str, str, Path, str, str, str]],
        backends: object,
        **kwargs: object,
    ) -> list[Measurement]:
        del config, oracle, backends
        captured_specs.extend(specs)
        result = measured(
            specs[0][2],
            variant_id=specs[0][1],
            compensation=specs[0][3],
            error=0.005,
        )
        callback = kwargs.get("on_result")
        if callable(callback):
            callback(result)
        return [result]

    monkeypatch.setattr(pipeline, "require_automation_skills", lambda: None)
    monkeypatch.setattr(pipeline, "_skill_records", lambda: [])
    monkeypatch.setattr(pipeline, "build_oracle", fake_oracle)
    monkeypatch.setattr(pipeline, "plan_strategies", fake_plan)
    monkeypatch.setattr(pipeline, "generate_candidate", fake_generate)
    monkeypatch.setattr(pipeline, "build_backends", lambda *_: [])
    monkeypatch.setattr(pipeline, "measure_variants", fake_measure_base)
    monkeypatch.setattr(pipeline, "generate_compensation", fake_compensation)
    monkeypatch.setattr(pipeline, "measure_compensation_variants", fake_measure_compensation)

    code, run_dir = asyncio.run(pipeline.run_pipeline(config_path))
    record = json.loads((run_dir / "run.json").read_text())
    assert code == 0
    assert len(record["compensation_variants"]) == 1
    assert record["numerical_candidates"][0]["candidate_id"] == "n-c1-fp16"
    assert record["numerical_candidates"][0]["parent_candidate_id"] == "c1"
    assert captured_specs[0][4:] == ("portable", "fp16")
    assert record["security"]["execution_mode"] == "trusted_local_unsandboxed"
    assert record["visualizations"]["overall"]["frontier_points"] == 1
    assert (run_dir / "visualizations" / "pareto-overall.svg").is_file()
    assert (run_dir / "visualizations" / "pareto-cpu.svg").is_file()
    assert (run_dir / "visualizations" / "frontiers.json").is_file()
    assert "Pareto plots: [overall]" in (run_dir / "summary.md").read_text()
    graph = (run_dir / "pipeline-graph.mmd").read_text()
    assert "direction LR" in graph
    assert "stream_candidates" in graph

    async def unexpected(*_: object, **__: object) -> object:
        raise AssertionError("completed work must not run again during resume")

    monkeypatch.setattr(pipeline, "build_oracle", unexpected)
    monkeypatch.setattr(pipeline, "plan_strategies", unexpected)
    monkeypatch.setattr(pipeline, "generate_candidate", unexpected)
    monkeypatch.setattr(pipeline, "build_backends", unexpected)
    resumed_code, resumed_dir = asyncio.run(pipeline.run_pipeline(config_path, resume_dir=run_dir))
    resumed = json.loads((resumed_dir / "run.json").read_text())
    assert resumed_code == 0
    assert resumed_dir == run_dir
    assert len(resumed["measurements"]) == 2


def test_pipeline_graph_declares_typed_orchestration_phases() -> None:
    diagram = pipeline.PIPELINE_GRAPH.render(direction="LR")
    phases = ("build_oracle", "plan_strategies", "stream_candidates", "finalize")
    assert all(phase in diagram for phase in phases)
    assert "plan_strategies --> stream_candidates" in diagram
    assert "stream_candidates --> finalize" in diagram


def test_pipeline_graph_takes_compensation_bypass_when_no_point_is_weak(
    tmp_path: Path, monkeypatch: Any
) -> None:
    data = minimal_config(tmp_path)
    data["runs_dir"] = str(tmp_path / "runs")
    data["compensation"] = {"error_threshold": 0.01, "measurement_scope": "all"}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    base_point = measured(module, variant_id="c1-base", compensation="none", error=0.005)

    async def fake_oracle(config: object, run_dir: object) -> OracleResult:
        del config, run_dir
        return OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def fake_plan(*_: object) -> tuple[list[str], dict[str, object]]:
        return ["direct"], {"text": "plan", "usage": {}}

    async def fake_generate(*_: object) -> Candidate:
        return candidate

    async def fake_measure_base(*_: object, **kwargs: object) -> list[Measurement]:
        callback = kwargs.get("on_result")
        if callable(callback):
            callback(base_point)
        return [base_point]

    async def reject_generation(*_: object) -> CompensationVariant:
        raise AssertionError("compensation branch should not run")

    async def fake_measure_compensation(
        config: object,
        oracle: object,
        specs: list[tuple[str, str, Path, str, str, str]],
        backends: object,
        **kwargs: object,
    ) -> list[Measurement]:
        del config, oracle, backends
        assert specs == []
        return []

    monkeypatch.setattr(pipeline, "require_automation_skills", lambda: None)
    monkeypatch.setattr(pipeline, "_skill_records", lambda: [])
    monkeypatch.setattr(pipeline, "build_oracle", fake_oracle)
    monkeypatch.setattr(pipeline, "plan_strategies", fake_plan)
    monkeypatch.setattr(pipeline, "generate_candidate", fake_generate)
    monkeypatch.setattr(pipeline, "build_backends", lambda *_: [])
    monkeypatch.setattr(pipeline, "measure_variants", fake_measure_base)
    monkeypatch.setattr(pipeline, "generate_compensation", reject_generation)
    monkeypatch.setattr(pipeline, "measure_compensation_variants", fake_measure_compensation)

    code, run_dir = asyncio.run(pipeline.run_pipeline(config_path))
    record = json.loads((run_dir / "run.json").read_text())
    assert code == 0
    assert record["compensation_variants"] == []
    assert len(record["measurements"]) == 1


def test_numerically_ineffective_compensation_is_rejected(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    base = measured(module, variant_id="c1-base", compensation="none", error=0.5)
    generated = measured(module, variant_id="c1-cpu-fp16", compensation="kahan", error=0.5)
    variant = CompensationVariant(
        "c1",
        "c1-cpu-fp16",
        "portable",
        "fp16",
        "kahan",
        module,
        status=Status.OK,
        target_backends=["cpu"],
    )
    pipeline._reject_non_improving_variants(config, [variant], [base], [generated])
    assert variant.status == Status.REJECTED
    assert variant.diagnostics[0].gate == "compensation-effect"
    assert generated.status == Status.REJECTED


@pytest.mark.parametrize("audit_fraction, expected_base_target_builds", [(0.0, 0), (1.0, 1)])
def test_gpu_screening_promotes_repair_before_target_builds(
    tmp_path: Path,
    monkeypatch: Any,
    audit_fraction: float,
    expected_base_target_builds: int,
) -> None:
    data = minimal_config(tmp_path)
    data["measure"] = {
        "precisions": ["fp32", "fp16"],
        "backends": [
            {
                "type": "torch",
                "name": "cuda",
                "device": "cuda",
                "precisions": ["fp32", "fp16"],
            },
            {
                "type": "native",
                "name": "ipu",
                "resource": "ipu",
                "architecture": "graphcore_ipu",
                "precisions": ["fp16"],
                "worker": {"python": "python"},
            },
        ],
    }
    data["execution"] = {"resources": {"ipu": {}}}
    data["screening"] = {
        "backend": "cuda",
        "precisions": ["fp16"],
        "smoke_precision": "fp32",
        "audit_fraction": audit_fraction,
    }
    data["compensation"] = {"error_threshold": 0.01}
    config = RunConfig.model_validate(data)
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    repaired_module = tmp_path / "repaired.py"
    repaired_module.write_text(GOOD_MODULE.replace("return x\n", "return x + 0\n"))
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0]))
    oracle = OracleResult(oracle_path, np.asarray([1.0]))
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    outcome = pipeline.CandidateOutcome(candidate)
    (tmp_path / "progress").mkdir()
    deps = pipeline.PipelineDeps(
        config,
        tmp_path / "config.yaml",
        tmp_path,
        None,  # type: ignore[arg-type]
        PipelineScheduler(config.scheduler),
        "2026-01-01T00:00:00+00:00",
        time.perf_counter(),
    )
    backends: Any = [
        SimpleNamespace(spec=SimpleNamespace(name="cuda")),
        SimpleNamespace(spec=SimpleNamespace(name="ipu")),
    ]
    calls: list[tuple[Path, set[tuple[str, str]]]] = []
    compensation_calls = 0

    def point(
        path: Path,
        backend: str,
        precision: str,
        variant_id: str,
        compensation: str,
        error: float,
    ) -> Measurement:
        result = measured(path, variant_id=variant_id, compensation=compensation, error=error)
        result.backend = backend
        result.precision = precision
        result.storage_precision = precision
        result.operator_precision = precision
        result.accumulator_precision = precision
        result.output_precision = precision
        return result

    async def fake_measure(
        config: object,
        oracle: object,
        specs: list[tuple[str, str, Path, str]],
        backends: object,
        *,
        cells: set[tuple[str, str]],
        on_result: Any,
    ) -> list[Measurement]:
        del config, oracle, backends
        _, variant_id, path, compensation = specs[0]
        calls.append((path, cells))
        results = []
        for backend, precision in cells:
            error = 0.05 if backend == "cuda" and precision == "fp16" else 0.005
            result = point(path, backend, precision, variant_id, compensation, error)
            results.append(result)
            on_result(result)
        return results

    async def fake_compensation(*args: Any, **kwargs: Any) -> CompensationVariant:
        nonlocal compensation_calls
        del args, kwargs
        compensation_calls += 1
        variant = CompensationVariant(
            "c1",
            "n-c1-fp16",
            "portable",
            "fp16",
            "kahan",
            repaired_module,
            status=Status.OK,
            target_backends=["cuda"],
        )
        variant.target_measurements = [
            point(repaired_module, "cuda", "fp16", variant.variant_id, "kahan", 0.005)
        ]
        return variant

    monkeypatch.setattr(pipeline, "measure_variants", fake_measure)
    monkeypatch.setattr(pipeline, "generate_compensation", fake_compensation)
    result = asyncio.run(pipeline._screened_candidate_flow(deps, oracle, outcome, backends))

    ipu_calls = [(path, cells) for path, cells in calls if ("ipu", "fp16") in cells]
    assert sum(path == module for path, _ in ipu_calls) == expected_base_target_builds
    assert sum(path == repaired_module for path, _ in ipu_calls) == 1
    assert result.numerical_candidates[0].module_path == repaired_module
    assert result.numerical_candidates[0].target_precision == "fp16"

    measured_calls = len(calls)
    measurement_count = len(result.measurements)
    resumed = asyncio.run(pipeline._screened_candidate_flow(deps, oracle, result, backends))
    assert compensation_calls == 1
    assert len(calls) == measured_calls
    assert len(resumed.measurements) == measurement_count


def test_portable_compensation_rejects_cross_platform_regression(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    weak = measured(module, variant_id="c1-base", compensation="none", error=0.5)
    weak.backend = "cuda"
    healthy = measured(module, variant_id="c1-base", compensation="none", error=0.1)
    healthy.backend = "groq"
    improved = measured(module, variant_id="n-c1-fp16", compensation="kahan", error=0.2)
    improved.backend = "cuda"
    regressed = measured(module, variant_id="n-c1-fp16", compensation="kahan", error=0.2)
    regressed.backend = "groq"
    variant = CompensationVariant(
        "c1",
        "n-c1-fp16",
        "portable",
        "fp16",
        "kahan",
        module,
        status=Status.OK,
        target_backends=["cuda"],
        guard_backends=["groq"],
    )
    pipeline._reject_non_improving_variants(
        config, [variant], [weak, healthy], [improved, regressed]
    )
    assert variant.status == Status.REJECTED
    assert improved.status == Status.REJECTED
    assert regressed.status == Status.REJECTED


def test_acceptance_requires_every_configured_accelerator(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda",
            "precisions": ["fp16"],
        }
    )
    config = RunConfig.model_validate(data)
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    cpu = measured(module, variant_id="c1-base", compensation="none", error=0.0)
    acceptance = pipeline._acceptance(config, [cpu])
    assert acceptance["passed"] is False
    assert acceptance["backends"]["cuda"]["passed"] is False

    cuda = measured(module, variant_id="c1-base", compensation="none", error=0.1)
    cuda.backend = "cuda"
    acceptance = pipeline._acceptance(config, [cpu, cuda])
    assert acceptance["passed"] is True


def test_skill_record_version_comes_from_install_manifest(tmp_path: Path, monkeypatch: Any) -> None:
    root = tmp_path / "skills"
    skill = root / "one" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("role: test\n")
    (root / ".lassi-x-manifest.json").write_text(
        json.dumps({"schema_version": 1, "lassi_x_version": "9.8.7"})
    )
    monkeypatch.setattr(run_record, "install_root", lambda: root)
    monkeypatch.setattr(run_record, "AUTOMATION_SKILLS", ("one",))
    assert run_record.skill_records()[0]["version"] == "9.8.7"


def test_candidate_journal_rejects_unknown_schema(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    deps = pipeline.PipelineDeps(
        config,
        tmp_path / "config.yaml",
        tmp_path,
        None,  # type: ignore[arg-type]
        PipelineScheduler(config.scheduler),
        "2026-01-01T00:00:00+00:00",
        time.perf_counter(),
    )
    progress = tmp_path / "progress"
    progress.mkdir()
    (progress / "c1.json").write_text(json.dumps({"schema_version": 999}))
    with pytest.raises(ValueError, match="unsupported candidate checkpoint schema"):
        pipeline._load_candidate_journal(deps, "c1")


@pytest.mark.parametrize("passing_candidates", [0, 2])
@pytest.mark.parametrize("interrupted", [False, True])
def test_cpu_verified_pause_and_resume(
    tmp_path: Path, monkeypatch: Any, passing_candidates: int, interrupted: bool
) -> None:
    """CPU preparation needs no remote device; resume consumes its journals once."""
    (tmp_path / "tiny.c").write_text("reference fixture")
    data = minimal_config(tmp_path)
    data["runs_dir"] = str(tmp_path / "runs")
    data["execution"] = {
        "mode": "academy",
        "exchange_url": "https://unavailable.example/exchange",
        "default_resource": "remote",
        "resources": {"remote": {"endpoint_id": "unavailable", "workspace_root": "/remote/run"}},
    }
    data["measure"]["backends"] = [
        {
            "type": "native",
            "name": "ipu",
            "architecture": "graphcore_ipu",
            "resource": "remote",
            "precisions": ["fp16"],
            "worker": {"python": "/unavailable/python"},
        }
    ]
    data["compatibility"] = {
        "compile_targets": [{"target_id": "torch-mlir-tosa", "resource": "remote"}],
    }
    data["compensation"] = {"enabled": False}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    calls: list[str] = []
    context_configs: list[RunConfig] = []
    start = ExecutionContext.start
    interrupt_generation = interrupted

    async def fake_start(config: RunConfig, run_dir: Path) -> ExecutionContext:
        context_configs.append(config)
        # Simulate the remote execution context locally during the continuation.
        return await start(config.model_copy(update={"execution": ExecutionConfig()}), run_dir)

    async def fake_oracle(*_: object) -> OracleResult:
        calls.append("oracle")
        return OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def fake_plan(*_: object) -> tuple[list[str], dict[str, object]]:
        calls.append("plan")
        return ["direct"] * 3, {}

    async def fake_generate(
        config: RunConfig,
        oracle: OracleResult,
        run_dir: Path,
        execution: ExecutionContext,
        index: int,
        strategy: str,
    ) -> Candidate:
        calls.append(f"generate-{index}")
        if interrupt_generation and index == 3:
            raise RuntimeError("CPU preparation interrupted")
        module = execution.workspace_dir(f"c{index}") / "candidate.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text(GOOD_MODULE)
        return Candidate(
            f"c{index}",
            "model",
            None,
            strategy,
            module,
            status=Status.OK if index <= passing_candidates else Status.REJECTED,
        )

    async def fake_preflight(*_: object) -> tuple[bool, dict[str, Any]]:
        calls.append("preflight")
        return True, {}

    async def fake_qualify(
        config: RunConfig,
        execution: ExecutionContext,
        candidate: Candidate,
        target: Any,
        precision: str,
    ) -> QualificationResult:
        calls.append(f"qualify-{candidate.candidate_id}")
        return QualificationResult(
            candidate.candidate_id,
            target.target_id,
            precision,
            True,
            "compiled",
            "remote",
        )

    async def fake_measure(*args: Any, **kwargs: Any) -> list[Measurement]:
        candidate_id, variant_id, module, compensation = args[2][0]
        calls.append(f"measure-{candidate_id}")
        point = measured(module, variant_id=variant_id, compensation=compensation, error=0.01)
        point.candidate_id = candidate_id
        point.backend = "ipu"
        kwargs["on_result"](point)
        return [point]

    monkeypatch.setattr(pipeline, "require_automation_skills", lambda: None)
    monkeypatch.setattr(pipeline, "_skill_records", lambda: [])
    monkeypatch.setattr(ExecutionContext, "start", fake_start)
    monkeypatch.setattr(pipeline, "build_oracle", fake_oracle)
    monkeypatch.setattr(pipeline, "plan_strategies", fake_plan)
    monkeypatch.setattr(pipeline, "generate_candidate", fake_generate)
    monkeypatch.setattr(pipeline, "native_runtime_checks", fake_preflight)
    monkeypatch.setattr(pipeline, "qualify_candidate", fake_qualify)
    monkeypatch.setattr(pipeline, "build_backends", lambda *_: [])
    monkeypatch.setattr(pipeline, "measure_variants", fake_measure)

    args = build_parser().parse_args(["run", str(config_path), "--until", "cpu-verified"])
    resume_dir = None
    if interrupted:
        failed_code, resume_dir = asyncio.run(pipeline.run_pipeline(args.config, until=args.until))
        assert failed_code == 1
        assert "--until cpu-verified" in (resume_dir / "summary.md").read_text()
        for index in (1, 2):
            assert (resume_dir / "progress" / f"c{index}.json").exists()
        interrupt_generation = False
        calls.clear()
    code, run_dir = asyncio.run(
        pipeline.run_pipeline(args.config, until=args.until, resume_dir=resume_dir)
    )
    assert code == (0 if passing_candidates else 1)
    assert context_configs[0].execution.mode == "local"
    assert context_configs[0].execution.resources == {}
    assert sorted(calls) == (
        ["generate-3"]
        if interrupted
        else ["generate-1", "generate-2", "generate-3", "oracle", "plan"]
    )
    record = json.loads((run_dir / "run.json").read_text())
    assert record["status"] == ("cpu_verified" if passing_candidates else "failed")
    assert len(record["candidates"]) == 3
    assert record["accuracy"]["final_passes"] == passing_candidates
    assert record["measurements"] == []
    checkpoint = json.loads((run_dir / "checkpoint.json").read_text())
    assert "cpu_verified" in checkpoint["completed_stages"]
    assert "stream_candidates" not in checkpoint["completed_stages"]
    assert "finalize" not in checkpoint["completed_stages"]
    assert checkpoint["completed_candidate_ids"] == []
    assert not (run_dir / "native-runtime-preflight.json").exists()
    assert not (run_dir / "frontier.json").exists()

    manifest_bytes = (run_dir / "cpu-baseline" / "manifest.json").read_bytes()
    if passing_candidates:
        fork_config = RunConfig.load(config_path)
        fork_config.models.planner.model = "different-planner"
        fork_dir = tmp_path / "fork"
        fork_dir.mkdir()
        imported = pipeline._import_cpu_baseline(
            run_dir, fork_config, fork_dir, allow_adaptations=False
        )
        assert len(imported.strategies) == passing_candidates
        assert imported.oracle is not None
        assert imported.oracle.output_path.parent == fork_dir / "baseline-inputs"
        provenance = json.loads((fork_dir / "cpu-baseline-provenance.json").read_text())
        assert provenance["frozen_candidates"]
        assert provenance["manifest_sha256"]
        journal = json.loads((fork_dir / "progress" / "c1.json").read_text())
        copied_module = fork_dir / "baseline-inputs" / "c1.py"
        assert journal["outcome"]["candidate"]["module_path"] == str(copied_module)
        copied_module.write_text("modified independent copy")
        assert (run_dir / "cpu-baseline" / "c1.py").read_text() == GOOD_MODULE
        mismatched = fork_config.model_copy(deep=True)
        mismatched.kernel.task = "different problem"
        with pytest.raises(ValueError, match="contract does not match"):
            pipeline._import_cpu_baseline(
                run_dir, mismatched, tmp_path / "bad-contract", allow_adaptations=False
            )
        baseline_module = run_dir / "cpu-baseline" / "c1.py"
        baseline_module.write_text("tampered")
        with pytest.raises(ValueError, match="checksum mismatch"):
            pipeline._import_cpu_baseline(
                run_dir, fork_config, tmp_path / "tampered", allow_adaptations=False
            )
        baseline_module.write_text(GOOD_MODULE)
    else:
        with pytest.raises(ValueError, match="no passing candidates"):
            pipeline._import_cpu_baseline(
                run_dir, RunConfig.load(config_path), tmp_path / "empty", allow_adaptations=False
            )

    calls.clear()
    repeated_code, repeated_dir = asyncio.run(
        pipeline.run_pipeline(config_path, resume_dir=run_dir, until="cpu-verified")
    )
    assert repeated_code == code
    assert repeated_dir == run_dir
    assert calls == []
    assert (run_dir / "cpu-baseline" / "manifest.json").read_bytes() == manifest_bytes

    if passing_candidates:
        fork_data = {**data, "compensation": {"enabled": True, "error_threshold": 0.001}}
        fork_data["models"] = {**data["models"], "planner": {"model": "other-planner"}}
        fork_path = tmp_path / "accelerator-ablation.yaml"
        fork_path.write_text(yaml.safe_dump(fork_data))
        fork_code, fork_run = asyncio.run(
            pipeline.run_pipeline(fork_path, from_cpu_baseline=run_dir)
        )
        assert fork_code == 0
        assert fork_run != run_dir
        assert not any(call.startswith("generate") or call in {"oracle", "plan"} for call in calls)
        fork_report = json.loads((fork_run / "run.json").read_text())
        assert len(fork_report["candidates"]) == passing_candidates
        assert not fork_report["compensation_variants"]
        calls.clear()
        assert asyncio.run(pipeline.run_pipeline(fork_path, resume_dir=fork_run))[0] == 0
        assert calls == ["preflight"]
        assert (run_dir / "cpu-baseline" / "manifest.json").read_bytes() == manifest_bytes

    changed = dict(data)
    changed["kernel"] = {**data["kernel"], "task": "A different task"}
    config_path.write_text(yaml.safe_dump(changed))
    with pytest.raises(ValueError, match="resume configuration does not match"):
        asyncio.run(pipeline.run_pipeline(config_path, resume_dir=run_dir))
    config_path.write_text(yaml.safe_dump(data))

    calls.clear()
    code, resumed_dir = asyncio.run(pipeline.run_pipeline(config_path, resume_dir=run_dir))
    assert resumed_dir == run_dir
    assert code == (0 if passing_candidates else 1)
    assert context_configs[-1].execution.mode == "academy"
    assert sorted(calls) == sorted(
        [
            "preflight",
            *[f"qualify-c{i}" for i in range(1, passing_candidates + 1)],
            *[f"measure-c{i}" for i in range(1, passing_candidates + 1)],
        ]
    )
    resumed = json.loads((run_dir / "run.json").read_text())
    assert len(resumed["candidates"]) == 3
    assert len(resumed["measurements"]) == passing_candidates
    assert "finalize" in resumed["checkpoint"]["completed_stages"]
