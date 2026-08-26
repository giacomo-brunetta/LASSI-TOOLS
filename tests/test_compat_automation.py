from __future__ import annotations

import subprocess
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast

import pytest
import torch

from compat_tool.checker_groq import GroqFlowChecker
from compat_tool.checker_inductor import InductorChecker

if TYPE_CHECKING:
    from pathlib import Path

from compat_tool.inventory import build_manifest, eligibility, prepare_from_checkout
from compat_tool.io import atomic_json, load_json
from compat_tool.probe import run_probe
from compat_tool.publish import build_snapshot, publish_snapshot
from compat_tool.query_wiki import LEGACY_TARGET, list_targets, load_snapshot, search_target_ops
from compat_tool.target import load_target

MM_META = {
    "mlir_name": "torch.aten.mm",
    "args": [
        {"name": "self", "type": "AnyTorchTensorType"},
        {"name": "mat2", "type": "AnyTorchTensorType"},
    ],
    "returns": [{"name": "result", "type": "AnyTorchTensorType"}],
}
ADD_META = {
    "mlir_name": "torch.aten.add.Tensor",
    "args": [
        {"name": "self", "type": "AnyTorchTensorType"},
        {"name": "other", "type": "AnyTorchTensorType"},
        {"name": "alpha", "type": "AnyTorchScalarType"},
    ],
    "returns": [{"name": "result", "type": "AnyTorchTensorType"}],
}
PRUNING: dict[str, dict[str, str]] = {"include": {}, "exclude": {}}


def test_eligibility_keeps_tensor_forward_and_prunes_other_contracts() -> None:
    assert eligibility("aten.mm", MM_META, PRUNING) == (True, None)
    assert eligibility("aten.mm_backward", MM_META, PRUNING)[0] is False
    assert eligibility("aten.add_.Tensor", ADD_META, PRUNING)[0] is False
    assert (
        eligibility(
            "aten.rand",
            {"args": [], "returns": [{"name": "result", "type": "AnyTorchTensorType"}]},
            PRUNING,
        )[0]
        is False
    )


def test_manifest_distinguishes_invalid_fixture_from_compiler_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid(*args: object, **kwargs: object) -> dict[str, object]:
        return {"status": "needs_fixture", "input_spec": None, "error": "bad contract"}

    monkeypatch.setattr("compat_tool.inventory.validate_recipe", invalid)
    manifest = build_manifest(
        {"aten.mm": MM_META},
        source={"revision": "test"},
        pruning=PRUNING,
        precisions=["fp32"],
    )
    case = manifest["operators"]["aten.mm"]["cases"]["fp32"]["canonical"]
    assert case["validation"]["status"] == "needs_fixture"
    assert manifest["summary"]["needs_fixture"] == 1
    assert manifest["summary"]["not_applicable"] == 0


def test_intrinsically_integral_operator_is_not_mislabeled_as_fp32() -> None:
    meta = {
        "mlir_name": "torch.aten.bitwise_not",
        "args": [{"name": "self", "type": "AnyTorchTensorType"}],
        "returns": [{"name": "result", "type": "AnyTorchTensorType"}],
    }
    manifest = build_manifest(
        {"aten.bitwise_not": meta},
        source={"revision": "test"},
        pruning=PRUNING,
        precisions=["fp32"],
    )
    validation = manifest["operators"]["aten.bitwise_not"]["cases"]["fp32"]["canonical"][
        "validation"
    ]
    assert validation["status"] == "not_applicable"
    assert validation["effective_input_dtypes"] == ["int64"]


def _write_target(path: Path) -> None:
    path.write_text(
        """schema_version: 1
target_id: fake-test-target
family: test
checker: compat_tool.checker_fake:FakeChecker
precisions: [fp32]
timeout_s: 30
max_workers: 2
options:
  reject_ops: [aten.add.Tensor]
""",
        encoding="utf-8",
    )


def test_probe_publish_and_query_target_snapshot(tmp_path: Path) -> None:
    manifest = build_manifest(
        {"aten.add.Tensor": ADD_META, "aten.mm": MM_META},
        source={"project": "test", "revision": "abc"},
        pruning=PRUNING,
        precisions=["fp32"],
    )
    assert manifest["summary"]["needs_fixture"] == 0
    manifest_path = tmp_path / "manifest.json"
    target_path = tmp_path / "target.yaml"
    atomic_json(manifest_path, manifest)
    _write_target(target_path)

    probe = run_probe(manifest_path, target_path, tmp_path / "run")
    assert probe["complete"] is True
    assert probe["results"]["aten.mm|fp32|canonical"]["status"] == "compiled"
    assert probe["results"]["aten.add.Tensor|fp32|canonical"]["status"] == "compile_rejected"

    snapshot, snapshot_path, wiki_path = publish_snapshot(
        manifest_path, tmp_path / "run" / "results.json", tmp_path / "published"
    )
    assert snapshot["complete"] is True
    assert snapshot_path.is_file()
    assert (wiki_path / "aten.mm.md").is_file()
    loaded = load_json(snapshot_path)
    assert (
        loaded["operators"]["aten.mm"]["cases"]["fp32"]["canonical"]["result"]["status"]
        == "compiled"
    )
    assert search_target_ops(
        "fake-test-target",
        "mm",
        precision="fp32",
        supported=True,
        snapshot_dir=tmp_path / "published" / "snapshots",
    ) == ["aten.mm"]


def test_snapshot_marks_missing_results_incomplete() -> None:
    manifest = build_manifest(
        {"aten.mm": MM_META},
        source={"revision": "test"},
        pruning=PRUNING,
        precisions=["fp32"],
    )
    probe = {
        "manifest_hash": manifest["manifest_hash"],
        "target_hash": "target",
        "target": {"target_id": "fake", "family": "test", "precisions": ["fp32"]},
        "environment": {},
        "results": {},
    }
    snapshot = build_snapshot(manifest, probe)
    assert snapshot["complete"] is False
    assert snapshot["summary"]["missing_results"] == 1


def test_target_validation_and_legacy_listing(tmp_path: Path) -> None:
    target_path = tmp_path / "target.yaml"
    _write_target(target_path)
    assert load_target(target_path)["target_id"] == "fake-test-target"
    assert list_targets(tmp_path)[0]["target_id"] == LEGACY_TARGET
    assert load_snapshot(LEGACY_TARGET)["legacy"] is True


def test_prepare_requires_exact_torch_mlir_revision(tmp_path: Path) -> None:
    checkout = tmp_path / "torch-mlir"
    ops_path = checkout / "include/torch-mlir/Dialect/Torch/IR"
    ops_path.mkdir(parents=True)
    (ops_path / "GeneratedTorchOps.td").write_text(
        """def Torch_AtenMmOp : Torch_Op<"aten.mm", [Pure]> {
let arguments = (ins AnyTorchTensorType:$self, AnyTorchTensorType:$mat2);
let results = (outs AnyTorchTensorType:$result);
}
""",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    subprocess.run(["git", "add", "."], cwd=checkout, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Compatibility Test",
            "-c",
            "user.email=compat@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=checkout,
        check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    output = tmp_path / "manifest.json"
    manifest = prepare_from_checkout(
        checkout,
        revision,
        output,
        precisions=["fp32"],
    )
    assert manifest["summary"] == {
        "operators": 1,
        "included": 1,
        "excluded": 0,
        "needs_fixture": 0,
        "not_applicable": 0,
    }
    with pytest.raises(ValueError, match="expected exact revision"):
        prepare_from_checkout(checkout, "0" * 40, output, precisions=["fp32"])


def test_inductor_checker_forces_one_compile_trigger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []

    def fake_compile(module: object, **kwargs: object) -> object:
        calls.append(kwargs)
        return module

    monkeypatch.setattr(torch, "compile", fake_compile)
    checker = InductorChecker(
        {
            "options": {
                "device": "cpu",
                "backend": "inductor",
                "fullgraph": True,
                "dynamic": False,
            }
        }
    )
    result = checker.compile(
        torch.nn.Identity(),
        (torch.ones(2),),
        op_name="aten.alias",
        precision="fp32",
        case_hash="abc",
        work_dir=tmp_path,
    )
    assert result["status"] == "compiled"
    assert result["compile_trigger"] == "one untimed invocation"
    assert calls == [{"backend": "inductor", "fullgraph": True, "dynamic": False}]


def test_groq_checker_stops_after_groqit_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    module = ModuleType("groqflow")
    module_api = cast("Any", module)
    module_api.__version__ = "test"

    def fake_groqit(model: object, inputs: dict[str, object], **kwargs: object) -> object:
        calls.append({"model": model, "inputs": inputs, **kwargs})
        return object()

    module_api.groqit = fake_groqit
    monkeypatch.setitem(sys.modules, "groqflow", module)
    checker = GroqFlowChecker({"options": {"trace_dtype": "float32", "cache_dir": str(tmp_path)}})
    result = checker.compile(
        torch.nn.Identity(),
        (torch.ones(2, dtype=torch.float16),),
        op_name="aten.alias",
        precision="fp16",
        case_hash="abc",
        work_dir=tmp_path,
    )
    assert result["status"] == "compiled"
    assert "no inference executed" in result["compile_trigger"]
    assert calls[0]["inputs"]["input0"].dtype == torch.float32
