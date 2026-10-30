from __future__ import annotations

import importlib
import json
import sys
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import torch

from lassi_x import input_contract
from lassi_x.input_contract import InputContractError, save_contract

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("valid", [True, False])
def test_groq_checks_fp16_values_before_compilation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid: bool
) -> None:
    sdk = ModuleType("groqflow")
    sdk.groqit = lambda *a, **k: object()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "groqflow", sdk)
    monkeypatch.setitem(sys.modules, "lassi_input_contract", input_contract)
    worker = importlib.import_module("lassi_x.groq_measure_worker")
    called = []

    def compile_model(*args: Any, **kwargs: Any) -> object:
        called.append(True)
        return object()

    monkeypatch.setattr(worker, "groqit", compile_model)

    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x

    def build_inputs(device: str, dtype: torch.dtype) -> tuple[torch.Tensor]:
        return (torch.tensor([1.1 if valid else 8.0], dtype=torch.float64).to(dtype),)

    contract = tmp_path / "inputs.npz"
    save_contract(contract, {"x": np.asarray([1.1])}, {"kernel": "example", "required": ["x"]})
    args = SimpleNamespace(
        input_contract=contract,
        input_snapshot=tmp_path / "snapshot.npz",
        input_bindings="{}",
        input_rtol=1e-12,
        input_atol=1e-14,
    )
    module = SimpleNamespace(make_model=Model, build_inputs=build_inputs)
    inputs = worker._inputs_for_dataset(module, "mini", torch.float16)
    assert inputs[0].dtype == torch.float32  # SDK transport, with exact FP16 values.
    if valid:
        worker._compile(
            module, inputs, build_name="test", cache_dir=tmp_path, input_check_args=args
        )
        assert called
    else:
        with pytest.raises(InputContractError):
            worker._compile(
                module, inputs, build_name="test", cache_dir=tmp_path, input_check_args=args
            )
        assert not called


@pytest.mark.parametrize("actual_direct", [True, False])
def test_groq_midpoint_input_check_uses_one_cast_on_older_torch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, actual_direct: bool
) -> None:
    sdk = ModuleType("groqflow")
    sdk.groqit = lambda *a, **k: object()
    monkeypatch.setitem(sys.modules, "groqflow", sdk)
    monkeypatch.setitem(sys.modules, "lassi_input_contract", input_contract)
    worker = importlib.import_module("lassi_x.groq_measure_worker")
    monkeypatch.setattr(worker, "groqit", lambda *a, **k: object())
    values = np.array([1.00048828125 + 2**-30], dtype=np.float64)
    direct = values.astype(np.float16)
    double = values.astype(np.float32).astype(np.float16)
    assert not np.array_equal(direct, double)
    bad_round = lambda value, precision: np.asarray(value, dtype=np.float64).astype(np.float32).astype(np.float16).astype(np.float64)
    monkeypatch.setattr(input_contract, "round_input_values", bad_round)

    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x

    contract = tmp_path / "inputs.npz"
    save_contract(contract, {"x": values}, {"kernel": "midpoint", "required": ["x"]})
    args = SimpleNamespace(input_contract=contract, input_snapshot=tmp_path / "snapshot.npz",
        input_bindings="{}", input_rtol=1e-12, input_atol=1e-14)
    module = SimpleNamespace(make_model=Model)
    inputs = (torch.from_numpy(direct if actual_direct else double).float(),)
    if actual_direct:
        worker._compile(module, inputs, build_name="midpoint", cache_dir=tmp_path, input_check_args=args)
    else:
        with pytest.raises(InputContractError):
            worker._compile(module, inputs, build_name="midpoint", cache_dir=tmp_path, input_check_args=args)
    assert input_contract.round_input_values is bad_round


def test_graphcore_rejects_inputs_before_sdk_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "popart", ModuleType("popart"))
    monkeypatch.setitem(sys.modules, "lassi_input_contract", input_contract)
    worker = importlib.import_module("lassi_x.graphcore_measure_worker")
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "import torch\n"
        "def build_inputs(device,dtype): return (torch.tensor([8.],dtype=dtype),)\n"
        "class Model(torch.nn.Module):\n"
        "    def forward(self,x): raise AssertionError('export must not run')\n"
        "def make_model(): return Model()\n"
    )
    contract = tmp_path / "inputs.npz"
    save_contract(contract, {"x": np.asarray([1.1])}, {"kernel": "example", "required": ["x"]})
    output = tmp_path / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "worker",
            "--architecture",
            "graphcore_ipu",
            "--module",
            str(candidate),
            "--oracle",
            str(tmp_path / "unused.npy"),
            "--output",
            str(output),
            "--precision",
            "fp16",
            "--input-contract",
            str(contract),
            "--input-snapshot",
            str(tmp_path / "snapshot.npz"),
        ],
    )
    assert worker.main() == 1
    result = json.loads(output.read_text())
    assert not result["ok"]
    assert result["phase"] == "inputs"
