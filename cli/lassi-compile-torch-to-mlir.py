#!/usr/bin/env python3
"""Compile a PyTorch .pt model into MLIR using torch-mlir."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-path", required=True, help="Path to the .pt model file.")
    add_json_arg(p, "inputs",
                 "List of input specs, e.g. [{\"shape\":[1,3,224,224],\"dtype\":\"float32\"}].",
                 required=True)
    p.add_argument("--target", default="linalg-on-tensors",
                   choices=["torch", "linalg", "linalg-on-tensors", "tosa", "stablehlo"])
    p.add_argument("--frontend", default="torchscript",
                   choices=["torchscript", "fx", "export"])
    p.add_argument("--no-validate", action="store_true",
                   help="Skip the dry forward pass before compiling.")
    p.add_argument("--output-path", default=None,
                   help="Optional path to save the generated MLIR.")
    a = p.parse_args()
    from lassi.integrations.torch_to_mlir import compile_torch_to_mlir_impl
    return run_async(compile_torch_to_mlir_impl(
        model_path=a.model_path,
        inputs=get_json_arg(a, "inputs"),
        target=a.target,
        frontend=a.frontend,
        validate=not a.no_validate,
        output_path=a.output_path,
    ), title="Torch → MLIR compilation")


if __name__ == "__main__":
    raise SystemExit(main())
