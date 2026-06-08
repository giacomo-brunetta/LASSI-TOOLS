#!/usr/bin/env python3
"""Load a PyTorch model from a Python file and export it to a .pt file."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-file", required=True, help="Path to Python file containing the model class.")
    p.add_argument("--class-name", required=True, help="Name of the model class to instantiate.")
    p.add_argument("--output-path", required=True, help="Path to save the exported .pt file.")
    add_json_arg(p, "init-args", "Constructor arguments for the model (JSON dict).")
    p.add_argument("--weights-path", default=None, help="Optional path to state_dict weights (.pth).")
    p.add_argument("--export-type", default="torchscript",
                   choices=["torchscript", "state_dict", "full"])
    add_json_arg(p, "input-shape", "Required for tracing if scripting fails (JSON list).")
    a = p.parse_args()
    from lassi.integrations.export_pt import export_model_to_pt_impl
    return run_async(export_model_to_pt_impl(
        model_file=a.model_file,
        class_name=a.class_name,
        output_path=a.output_path,
        init_args=get_json_arg(a, "init-args"),
        weights_path=a.weights_path,
        export_type=a.export_type,
        input_shape=get_json_arg(a, "input-shape"),
    ), title="PyTorch .pt export")


if __name__ == "__main__":
    raise SystemExit(main())
