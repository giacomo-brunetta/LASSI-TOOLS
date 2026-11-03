"""Trusted subprocess checks for the bounded Luna replanning example."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten

from lassi_x.candidate_runner import PRECISIONS, load_module
from lassi_x.input_contract import check_worker_inputs
from lassi_x.validation import compare_outputs, load_reference_output


class PromotionAudit(TorchDispatchMode):  # type: ignore[no-untyped-call]
    """Inventory explicit wider tensor operations on one executed forward."""

    def __init__(self, dtype: torch.dtype) -> None:
        super().__init__()  # type: ignore[no-untyped-call]
        self.dtype = dtype
        self.wider_ops: set[str] = set()
        self.host_scalar = False

    def _wide(self, values: Any) -> bool:
        return any(
            isinstance(item, torch.Tensor)
            and (item.is_floating_point() or item.is_complex())
            and item.dtype != self.dtype
            for item in tree_flatten(values)[0]
        )

    def __torch_dispatch__(self, func: Any, types: Any, args: Any = (), kwargs: Any = None) -> Any:
        kwargs = kwargs or {}
        if "_local_scalar_dense" in str(func) and any(
            isinstance(item, torch.Tensor) and item.is_floating_point()
            for item in tree_flatten(args)[0]
        ):
            self.host_scalar = True
        wide_input = self._wide((args, kwargs))
        result = func(*args, **kwargs)
        if wide_input or self._wide(result):
            self.wider_ops.add(str(func))
        return result


def _inputs(module: Any, dtype: torch.dtype, device: str) -> tuple[torch.Tensor, ...]:
    return tuple(module.build_inputs(device=device, dtype=dtype, dataset="mini"))


def audit(module_path: Path, precision: str, device: str) -> dict[str, Any]:
    dtype = PRECISIONS[precision]
    module = load_module(module_path)
    model = module.make_model().to(device=device, dtype=dtype).eval()
    inputs = _inputs(module, dtype, device)
    inspector = PromotionAudit(dtype)
    with torch.no_grad(), inspector:
        output = model(*inputs)
    outputs = tree_flatten(output)[0]
    wrong_output = [
        str(item.dtype)
        for item in outputs
        if isinstance(item, torch.Tensor) and item.is_floating_point() and item.dtype != dtype
    ]
    return {
        "protocol": "executed-explicit-op-inventory-demo-v1",
        "source_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
        "precision": precision,
        "device": device,
        "promoted_operations": sorted(inspector.wider_ops),
        "host_scalar": inspector.host_scalar,
        "wrong_output_dtypes": wrong_output,
        "complete": True,
        "scope": "one eager forward; implicit accumulation and compiled lowering unverified",
    }


def _flat(output: Any) -> tuple[np.ndarray, list[int]]:
    values = tree_flatten(output)[0]
    if not values or any(not isinstance(item, torch.Tensor) for item in values):
        raise TypeError("forward must return tensors")
    tensors = [item for item in values if isinstance(item, torch.Tensor)]
    return (
        np.concatenate([item.detach().cpu().double().numpy().reshape(-1) for item in tensors]),
        [item.numel() for item in tensors],
    )


def target(
    module_path: Path, oracle_path: Path, input_contract: Path, precision: str, device: str
) -> dict[str, Any]:
    dtype = PRECISIONS[precision]
    module = load_module(module_path)
    model = module.make_model().to(device=device, dtype=dtype).eval()
    inputs = _inputs(module, dtype, device)
    arguments = argparse.Namespace(
        input_contract=input_contract,
        input_bindings="{}",
        input_rtol=1e-12,
        input_atol=1e-14,
        input_snapshot=None,
        precision=precision,
    )
    input_check = check_worker_inputs(model, inputs, arguments)
    with torch.no_grad():
        traced = torch.jit.trace(  # type: ignore[no-untyped-call]
            model, inputs, strict=False, check_trace=False
        )
        traced(*inputs)
        if device == "mps":
            torch.mps.synchronize()
        samples: list[float] = []
        for _ in range(3):
            if device == "mps":
                torch.mps.synchronize()
            started = time.perf_counter()
            output = traced(*inputs)
            if device == "mps":
                torch.mps.synchronize()
            samples.append(time.perf_counter() - started)
    actual, component_sizes = _flat(output)
    if any(
        isinstance(item, torch.Tensor) and item.device.type != device
        for item in tree_flatten(output)[0]
    ):
        raise RuntimeError("compiled output left the target device")
    oracle = load_reference_output(oracle_path)
    passed, diagnostic, metrics = compare_outputs(
        actual,
        oracle,
        rtol=0.001,
        atol=1e-5,
        max_mismatches=20,
        component_sizes=component_sizes,
    )
    finite = bool(np.isfinite(actual).all())
    relative_l2 = float(metrics["relative_l2"])
    accurate = finite and relative_l2 <= 0.001
    return {
        "compile_result": "pass",
        "accuracy": {
            "failure": "pass" if accurate else "divergent" if not finite else "finite_error",
            "metrics": metrics,
            "diagnostics": ""
            if passed
            else diagnostic.message
            if diagnostic
            else "accuracy gate failed",
        },
        "input_check": input_check,
        "latency_s": statistics.median(samples) if accurate else None,
        "timing_scope": "host-synchronized MPS TorchScript call; compilation excluded",
        "precision_scope": "eager explicit operations only; compiled lowering unverified",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["audit", "target"])
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--precision", choices=["fp16", "bf16", "fp32"], required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--input-contract", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "audit":
            payload = audit(args.module, args.precision, args.device)
        else:
            if args.oracle is None or args.input_contract is None:
                raise ValueError("target check requires oracle and input contract")
            payload = target(
                args.module, args.oracle, args.input_contract, args.precision, args.device
            )
        print(json.dumps({"ok": True, **payload}))
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "error": str(exc)[:800]}))


if __name__ == "__main__":
    main()
