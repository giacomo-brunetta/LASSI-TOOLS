from __future__ import annotations

import subprocess
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast

import pytest
import torch

from lassi_x.compat.checkers.groq import GroqFlowChecker
from lassi_x.compat.checkers.inductor import InductorChecker
from lassi_x.compat.fixtures import validate_recipe

if TYPE_CHECKING:
    from pathlib import Path

from lassi_x.compat.case_builder import resolve_torch_schema
from lassi_x.compat.inventory import build_manifest, eligibility, prepare_from_checkout
from lassi_x.compat.io import atomic_json, load_json
from lassi_x.compat.probe import _worker_payload, run_probe
from lassi_x.compat.probe_worker import _probe
from lassi_x.compat.publish import build_snapshot, publish_snapshot
from lassi_x.compat.query_wiki import list_targets, load_snapshot, search_target_ops
from lassi_x.compat.target import load_target

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

    monkeypatch.setattr("lassi_x.compat.inventory.validate_recipe", invalid)
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


def test_low_precision_cpu_gap_uses_fp32_only_for_contract_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class HalfUnsupported(torch.nn.Module):
        def forward(self, value: torch.Tensor) -> torch.Tensor:
            del value
            raise RuntimeError("\"example_cpu\" not implemented for 'Half'")

    class FloatSupported(torch.nn.Module):
        def forward(self, value: torch.Tensor) -> torch.Tensor:
            return value + 1

    def fake_build_case(
        op_name: str, op_meta: dict[str, Any], recipe: dict[str, Any]
    ) -> tuple[torch.nn.Module, tuple[torch.Tensor, ...], str]:
        del op_name, op_meta
        dtype = getattr(torch, str(recipe["tensor_dtype"]))
        module = HalfUnsupported() if dtype == torch.float16 else FloatSupported()
        return module, (torch.ones(2, dtype=dtype),), f"value: dtype={dtype}"

    monkeypatch.setattr("lassi_x.compat.fixtures.build_case", fake_build_case)
    validation = validate_recipe(
        "aten.example",
        {"args": [], "returns": []},
        {"tensor_dtype": "float16", "seed": 0, "tensor_mode": "default"},
    )

    assert validation["status"] == "valid"
    assert validation["effective_input_dtypes"] == ["float16"]
    assert validation["validation_fallback_dtype"] == "float32"


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
checker: lassi_x.compat.checkers.fake:FakeChecker
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
        target_dir=tmp_path / "published" / "targets",
    ) == ["aten.mm"]


def test_vendor_frontend_system_exit_is_a_compile_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = build_manifest(
        {"aten.mm": MM_META},
        source={"revision": "test"},
        pruning=PRUNING,
        precisions=["fp32"],
    )

    class ExitingChecker:
        def __init__(self, target: dict[str, Any]) -> None:
            del target

        def compile(self, *args: object, **kwargs: object) -> dict[str, Any]:
            del args, kwargs
            raise SystemExit(0)

    monkeypatch.setattr("lassi_x.compat.probe_worker.checker_class", lambda target: ExitingChecker)
    result = _probe(
        {"target_id": "vendor-test"},
        manifest,
        "aten.mm",
        "fp32",
        "canonical",
        tmp_path,
    )

    assert result["status"] == "compile_rejected"
    assert result["error"] == "compiler frontend exited with status 0"


def test_clean_vendor_exit_without_worker_json_is_a_compile_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = subprocess.CompletedProcess(
        args=["vendor-compiler"], returncode=0, stdout="", stderr="unsupported graph"
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    result, returncode = _worker_payload(["vendor-compiler"], 30)

    assert returncode == 0
    assert result == {"status": "compile_rejected", "error": "unsupported graph"}


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


def test_target_validation_and_listing_includes_unpublished_config(tmp_path: Path) -> None:
    target_dir = tmp_path / "fake-test-target"
    target_dir.mkdir()
    target_path = target_dir / "target.yaml"
    _write_target(target_path)
    assert load_target(target_dir)["target_id"] == "fake-test-target"
    targets = list_targets(tmp_path)
    assert targets[0]["target_id"] == "fake-test-target"
    assert targets[0]["published"] is False


def test_tosa_results_are_a_regular_flat_support_target() -> None:
    snapshot = load_snapshot("torch-mlir-tosa")
    assert snapshot["result_format"] == "flat-support"
    assert snapshot["summary"] == {"operators": 689, "supported": 213, "unsupported": 476}
    assert search_target_ops("torch-mlir-tosa", "mm", supported=True)
    target = next(item for item in list_targets() if item["target_id"] == "torch-mlir-tosa")
    assert target["published"] is True
    assert target["result_format"] == "flat-support"


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


def test_schema_resolution_supports_pytorch_21_default_overload() -> None:
    schema = object()

    class DefaultOverload:
        _schema = schema

    class LegacyOverloadPacket:
        default = DefaultOverload()

    assert resolve_torch_schema("aten.mm", LegacyOverloadPacket()) is schema


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
