from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import torch


TORCH_DTYPE_MAP = {
    "float16": torch.float16,
    "float32": torch.float32,
    "float64": torch.float64,
    "bfloat16": torch.bfloat16,
    "int32": torch.int32,
    "int64": torch.int64,
    "bool": torch.bool,
}


def build_tensor_from_spec(spec: dict[str, Any]) -> torch.Tensor:
    shape = spec.get("shape")
    if not shape:
        raise ValueError("Tensor spec must include a non-empty 'shape'.")

    dtype_name = spec.get("dtype", "float32")
    if dtype_name not in TORCH_DTYPE_MAP:
        raise ValueError(f"Unsupported dtype in spec: {dtype_name}")

    dtype = TORCH_DTYPE_MAP[dtype_name]
    device_name = spec.get("device", "cpu")

    if "value" in spec:
        return torch.full(shape, spec["value"], dtype=dtype, device=device_name)
    if dtype in (torch.float16, torch.float32, torch.float64, torch.bfloat16):
        return torch.randn(*shape, dtype=dtype, device=device_name)
    if dtype in (torch.int32, torch.int64):
        return torch.randint(
            spec.get("low", 0),
            spec.get("high", 10),
            shape,
            dtype=dtype,
            device=device_name,
        )
    if dtype is torch.bool:
        return torch.randint(0, 2, shape, dtype=torch.int64, device=device_name).to(torch.bool)

    raise ValueError(f"Unsupported dtype in spec: {dtype_name}")


def build_inputs_from_specs(specs: list[dict[str, Any]]) -> tuple[torch.Tensor, ...]:
    return tuple(build_tensor_from_spec(spec) for spec in specs)


def build_trace_input(input_shape: list[Any]):
    if len(input_shape) > 0 and isinstance(input_shape[0], (list, tuple)):
        return tuple(torch.randn(*shape) for shape in input_shape)
    return torch.randn(*input_shape)


def load_module_from_file(path: str | Path, module_name: str | None = None):
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Module file not found: {resolved}")

    module_name = module_name or resolved.stem
    spec = importlib.util.spec_from_file_location(module_name, str(resolved))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for {resolved}")

    parent = str(resolved.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
