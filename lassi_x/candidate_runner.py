from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import torch

if TYPE_CHECKING:
    from types import ModuleType

PRECISIONS = {
    "fp64": torch.float64,
    "fp32": torch.float32,
    "fp16": torch.float16,
    "bf16": torch.bfloat16,
}


def load_module(path: Path) -> ModuleType:
    identity = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]
    name = f"lassi_x_candidate_{identity}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import candidate {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_module(
    module_path: Path,
    *,
    device: str,
    precision: str,
    fixture: Path | None = None,
    dataset: str = "default",
    input_contract: Path | None = None,
    input_report: Path | None = None,
    input_snapshot: Path | None = None,
    input_bindings: dict[str, str] | None = None,
    input_rtol: float = 1e-12,
    input_atol: float = 1e-14,
    inputs_only: bool = False,
) -> tuple[np.ndarray, str]:
    module = load_module(module_path)
    dtype = PRECISIONS[precision]
    direct = False
    arguments: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    if input_contract is not None:
        from .input_contract import load_contract, supplied_fixture_inputs  # noqa: PLC0415

        _, metadata = load_contract(input_contract)
        direct = metadata.get("schema_version") == 2
        if direct:
            arguments, metadata = supplied_fixture_inputs(
                input_contract, device=device, dtype=dtype
            )
    if callable(getattr(module, "make_model", None)):
        model = module.make_model()
    elif direct and callable(getattr(module, "forward", None)):
        model = module.forward
    else:
        raise TypeError("candidate must define make_model() or a fixture-backed forward()")
    inputs = ()
    if direct:
        inspect.signature(model.forward if hasattr(model, "forward") else model).bind(**arguments)
    else:
        if not callable(getattr(module, "build_inputs", None)):
            raise TypeError("candidate must define callable build_inputs(device, dtype)")
        kwargs = {"device": device, "dtype": dtype}
        if fixture is not None and "fixture" in inspect.signature(module.build_inputs).parameters:
            kwargs["fixture"] = fixture
        if "dataset" in inspect.signature(module.build_inputs).parameters:
            kwargs["dataset"] = dataset
        inputs = module.build_inputs(**kwargs)
        if not isinstance(inputs, tuple):
            raise TypeError("build_inputs must return a tuple")
    if hasattr(model, "eval"):
        model.eval()
    if hasattr(model, "to"):
        model.to(device)
    if input_contract is not None:
        from .input_contract import InputContractError, check_model_inputs  # noqa: PLC0415

        if direct:
            from .input_contract import compare_input_arrays  # noqa: PLC0415

            actual: dict[str, Any] = {
                name: value.detach().cpu().double().numpy()
                if isinstance(value, torch.Tensor) and value.dtype == torch.bfloat16
                else value.detach().cpu().numpy().copy()
                if isinstance(value, torch.Tensor)
                else np.asarray(value)
                for name, value in arguments.items()
            }
            expected, metadata = load_contract(input_contract)
            # Python integer scalars have no storage width; C arrays do.
            for name, item in metadata["inputs"].items():
                if item["scalar"]:
                    actual[item["argument"]] = np.asarray(
                        actual[item["argument"]], dtype=expected[name].dtype
                    )
            if input_snapshot is not None:
                input_snapshot.parent.mkdir(parents=True, exist_ok=True)
                np.savez(input_snapshot, **actual)
            report = compare_input_arrays(actual, expected, metadata, precision=precision)
        else:
            report = check_model_inputs(
                model,
                inputs,
                input_contract,
                bindings=input_bindings,
                rtol=input_rtol,
                atol=input_atol,
                snapshot_path=input_snapshot,
                precision=precision,
            )
        if input_report is not None:
            input_report.parent.mkdir(parents=True, exist_ok=True)
            input_report.write_text(json.dumps(report, indent=2) + "\n")
        if not report["ok"]:
            raise InputContractError(json.dumps(report["errors"]))
    if inputs_only:
        if input_contract is None:
            raise ValueError("--inputs-only requires --input-contract")
        return np.empty(0), ""
    protected = {
        item["argument"]: arguments[item["argument"]].clone()
        for item in metadata.get("inputs", {}).values()
        if direct
        and item["access"] == "read_only"
        and isinstance(arguments[item["argument"]], torch.Tensor)
    }
    with torch.no_grad():
        output = model(**arguments) if direct else model(*inputs)
    for name, original in protected.items():
        if not torch.equal(arguments[name], original):
            raise InputContractError(f"candidate modified read-only argument {name}")
    tensors = output if isinstance(output, tuple) else (output,)
    flattened: list[np.ndarray] = []
    output_dtype = ""
    for item in tensors:
        if not isinstance(item, torch.Tensor):
            raise TypeError("forward must return a tensor or tuple of tensors")
        output_dtype = str(item.dtype).removeprefix("torch.")
        flattened.append(item.detach().double().cpu().numpy().reshape(-1))
    return np.concatenate(flattened), output_dtype


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--precision", choices=sorted(PRECISIONS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--dataset", default="default")
    parser.add_argument("--input-contract", type=Path)
    parser.add_argument("--input-report", type=Path)
    parser.add_argument("--input-snapshot", type=Path)
    parser.add_argument("--input-bindings", default="{}")
    parser.add_argument("--input-rtol", type=float, default=1e-12)
    parser.add_argument("--input-atol", type=float, default=1e-14)
    parser.add_argument("--inputs-only", action="store_true")
    args = parser.parse_args()
    try:
        output, output_dtype = run_module(
            args.module,
            device=args.device,
            precision=args.precision,
            fixture=args.fixture,
            dataset=args.dataset,
            input_contract=args.input_contract,
            input_report=args.input_report,
            input_snapshot=args.input_snapshot,
            input_bindings=json.loads(args.input_bindings),
            input_rtol=args.input_rtol,
            input_atol=args.input_atol,
            inputs_only=args.inputs_only,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        np.save(args.output, output)
        print(
            json.dumps(
                {
                    "ok": True,
                    "shape": list(output.shape),
                    "numel": int(output.size),
                    "finite": bool(np.isfinite(output).all()),
                    "output_dtype": output_dtype,
                }
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "gate": "inputs" if type(exc).__name__ == "InputContractError" else "runtime",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
