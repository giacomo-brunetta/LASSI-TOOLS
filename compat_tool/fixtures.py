"""Deterministic, schema-aware canonical compatibility fixtures."""

# Keep wiki/inventory metadata importable without eagerly importing PyTorch.
# ruff: noqa: PLC0415

from __future__ import annotations

from typing import Any

PRECISION_DTYPES = {
    "fp64": "float64",
    "fp32": "float32",
    "fp16": "float16",
    "bf16": "bfloat16",
}

# Exact OpInfo mappings can be added without changing the manifest format.
# PyTorch's OpInfo package is optional and frequently unavailable in vendor
# environments, so only explicitly reviewed mappings belong here.
OPINFO_MAPPINGS: dict[str, str] = {}


def canonical_recipe(op_name: str, precision: str) -> dict[str, Any]:
    if precision not in PRECISION_DTYPES:
        raise ValueError(f"Unknown precision: {precision}")
    return {
        "name": "canonical",
        "provider": "opinfo" if op_name in OPINFO_MAPPINGS else "schema+overrides",
        "opinfo_name": OPINFO_MAPPINGS.get(op_name),
        "precision": precision,
        "tensor_dtype": PRECISION_DTYPES[precision],
        "tensor_mode": "default",
        "seed": 0,
    }


def build_case(
    op_name: str,
    op_meta: dict[str, Any],
    recipe: dict[str, Any],
) -> tuple[Any, tuple[Any, ...], str]:
    """Reconstruct a canonical module and positional inputs from a recipe."""
    import torch

    from compat_tool.utils import build_bound_invocation

    dtype_name = str(recipe["tensor_dtype"])
    dtype = getattr(torch, dtype_name)
    torch.manual_seed(int(recipe.get("seed", 0)))
    invocation, inputs, input_spec = build_bound_invocation(
        op_name,
        op_meta,
        tensor_dtype=dtype,
        tensor_mode=str(recipe.get("tensor_mode", "default")),
    )
    return invocation.build_module(), inputs, input_spec


def validate_recipe(
    op_name: str,
    op_meta: dict[str, Any],
    recipe: dict[str, Any],
) -> dict[str, Any]:
    """Eagerly execute one recipe so harness errors are not compiler failures."""
    import torch

    try:
        module, inputs, input_spec = build_case(op_name, op_meta, recipe)
        floating_dtypes = {
            str(value.dtype).removeprefix("torch.")
            for value in inputs
            if isinstance(value, torch.Tensor) and (value.is_floating_point() or value.is_complex())
        }
        requested_dtype = str(recipe["tensor_dtype"])
        if not floating_dtypes:
            return {
                "status": "not_applicable",
                "input_spec": input_spec,
                "error": "canonical operator inputs do not use floating-point tensors",
                "effective_input_dtypes": sorted(
                    {
                        str(value.dtype).removeprefix("torch.")
                        for value in inputs
                        if isinstance(value, torch.Tensor)
                    }
                ),
            }
        if requested_dtype not in floating_dtypes:
            raise TypeError(
                f"fixture does not exercise requested dtype {requested_dtype}; "
                f"effective floating dtypes are {sorted(floating_dtypes)}"
            )
        with torch.no_grad():
            output = module(*inputs)
        leaves = output if isinstance(output, (tuple, list)) else (output,)
        if not leaves or not any(isinstance(value, torch.Tensor) for value in leaves):
            raise TypeError("canonical invocation did not return a tensor")
        return {
            "status": "valid",
            "input_spec": input_spec,
            "error": None,
            "effective_input_dtypes": sorted(floating_dtypes),
        }
    except Exception as error:
        return {
            "status": "needs_fixture",
            "input_spec": None,
            "error": f"{type(error).__name__}: {error}",
        }
