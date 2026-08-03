from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import numpy as np
import yaml

import lassi_x.pipeline as pipeline
from lassi_x.compensation import CompensationVariant
from lassi_x.config import RunConfig
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
    )


def test_pipeline_compensates_single_high_error_survivor(tmp_path: Path, monkeypatch: Any) -> None:
    data = minimal_config(tmp_path)
    data["runs_dir"] = str(tmp_path / "runs")
    data["compensation"] = {"error_threshold": 0.1, "measurement_scope": "target"}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    base_point = measured(module, variant_id="c1-base", compensation="none", error=0.5)
    captured_specs: list[tuple[str, str, Path, str, str, str]] = []

    async def fake_oracle(config: object, run_dir: object) -> OracleResult:
        del config, run_dir
        return OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def fake_arena(*_: object) -> tuple[list[Candidate], dict[str, object]]:
        return [candidate], {"text": "plan", "usage": {}}

    async def fake_measure_base(*_: object) -> list[Measurement]:
        return [base_point]

    async def fake_compensation(
        config: object,
        oracle: object,
        run_dir: Path,
        execution: object,
        base: Candidate,
        weak: Measurement,
        backend: object,
    ) -> CompensationVariant:
        del config, oracle, execution, backend
        assert base is candidate
        assert weak is base_point
        target = run_dir / "variant.py"
        target.write_text(GOOD_MODULE.replace("return x\n", "return x + 0\n"))
        return CompensationVariant(
            "c1", "c1-cpu-fp16", "cpu", "fp16", "kahan", target, status=Status.OK
        )

    async def fake_measure_compensation(
        config: object,
        oracle: object,
        specs: list[tuple[str, str, Path, str, str, str]],
        backends: object,
    ) -> list[Measurement]:
        del config, oracle, backends
        captured_specs.extend(specs)
        return [
            measured(
                specs[0][2],
                variant_id=specs[0][1],
                compensation=specs[0][3],
                error=0.01,
            )
        ]

    monkeypatch.setattr(pipeline, "require_automation_skills", lambda: None)
    monkeypatch.setattr(pipeline, "_skill_records", lambda: [])
    monkeypatch.setattr(pipeline, "build_oracle", fake_oracle)
    monkeypatch.setattr(pipeline, "run_arena", fake_arena)
    monkeypatch.setattr(pipeline, "build_backends", lambda *_: [])
    monkeypatch.setattr(pipeline, "measure_variants", fake_measure_base)
    monkeypatch.setattr(pipeline, "generate_compensation", fake_compensation)
    monkeypatch.setattr(pipeline, "measure_compensation_variants", fake_measure_compensation)

    code, run_dir = asyncio.run(pipeline.run_pipeline(config_path))
    record = json.loads((run_dir / "run.json").read_text())
    assert code == 0
    assert len(record["compensation_variants"]) == 1
    assert captured_specs[0][4:] == ("cpu", "fp16")
    assert record["security"]["execution_mode"] == "trusted_local_unsandboxed"
    graph = (run_dir / "pipeline-graph.mmd").read_text()
    assert "direction LR" in graph
    assert "compensation_decision" in graph


def test_pipeline_graph_declares_typed_orchestration_phases() -> None:
    diagram = pipeline.PIPELINE_GRAPH.render(direction="LR")
    phases = (
        "build_oracle",
        "run_arena",
        "measure_base",
        "route_compensation",
        "generate_compensation",
        "skip_compensation",
        "measure_compensation",
        "finalize",
    )
    assert all(phase in diagram for phase in phases)
    assert "route_compensation --> compensation_decision" in diagram
    assert "generate_compensation --> measure_compensation" in diagram
    assert "skip_compensation --> measure_compensation" in diagram


def test_pipeline_graph_takes_compensation_bypass_when_no_point_is_weak(
    tmp_path: Path, monkeypatch: Any
) -> None:
    data = minimal_config(tmp_path)
    data["runs_dir"] = str(tmp_path / "runs")
    data["compensation"] = {"error_threshold": 0.1, "measurement_scope": "target"}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray([1.0, 2.0, 3.0]))
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    base_point = measured(module, variant_id="c1-base", compensation="none", error=0.01)

    async def fake_oracle(config: object, run_dir: object) -> OracleResult:
        del config, run_dir
        return OracleResult(oracle_path, np.asarray([1.0, 2.0, 3.0]))

    async def fake_arena(*_: object) -> tuple[list[Candidate], dict[str, object]]:
        return [candidate], {"text": "plan", "usage": {}}

    async def fake_measure_base(*_: object) -> list[Measurement]:
        return [base_point]

    async def reject_generation(*_: object) -> CompensationVariant:
        raise AssertionError("compensation branch should not run")

    async def fake_measure_compensation(
        config: object,
        oracle: object,
        specs: list[tuple[str, str, Path, str, str, str]],
        backends: object,
    ) -> list[Measurement]:
        del config, oracle, backends
        assert specs == []
        return []

    monkeypatch.setattr(pipeline, "require_automation_skills", lambda: None)
    monkeypatch.setattr(pipeline, "_skill_records", lambda: [])
    monkeypatch.setattr(pipeline, "build_oracle", fake_oracle)
    monkeypatch.setattr(pipeline, "run_arena", fake_arena)
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
        "c1", "c1-cpu-fp16", "cpu", "fp16", "kahan", module, status=Status.OK
    )
    pipeline._reject_non_improving_variants(config, [variant], [base], [generated])
    assert variant.status == Status.REJECTED
    assert variant.diagnostics[0].gate == "compensation-effect"
    assert generated.status == Status.REJECTED


def test_skill_record_version_comes_from_install_manifest(tmp_path: Path, monkeypatch: Any) -> None:
    root = tmp_path / "skills"
    skill = root / "one" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("role: test\n")
    (root / ".lassi-x-manifest.json").write_text(
        json.dumps({"schema_version": 1, "lassi_x_version": "9.8.7"})
    )
    monkeypatch.setattr(pipeline, "install_root", lambda: root)
    monkeypatch.setattr(pipeline, "AUTOMATION_SKILLS", ("one",))
    assert pipeline._skill_records()[0]["version"] == "9.8.7"
