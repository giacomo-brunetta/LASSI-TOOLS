from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

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
) -> tuple[np.ndarray, str]:
    module = load_module(module_path)
    if not callable(getattr(module, "build_inputs", None)):
        raise TypeError("candidate must define callable build_inputs(device, dtype)")
    if not callable(getattr(module, "make_model", None)):
        raise TypeError("candidate must define callable make_model()")
    dtype = PRECISIONS[precision]
    kwargs = {"device": device, "dtype": dtype}
    if fixture is not None and "fixture" in inspect.signature(module.build_inputs).parameters:
        kwargs["fixture"] = fixture
    if "dataset" in inspect.signature(module.build_inputs).parameters:
        kwargs["dataset"] = dataset
    inputs = module.build_inputs(**kwargs)
    if not isinstance(inputs, tuple):
        raise TypeError("build_inputs must return a tuple")
    model = module.make_model()
    if hasattr(model, "eval"):
        model.eval()
    if hasattr(model, "to"):
        model.to(device)
    with torch.no_grad():
        output = model(*inputs)
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
    args = parser.parse_args()
    try:
        output, output_dtype = run_module(
            args.module,
            device=args.device,
            precision=args.precision,
            fixture=args.fixture,
            dataset=args.dataset,
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
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
