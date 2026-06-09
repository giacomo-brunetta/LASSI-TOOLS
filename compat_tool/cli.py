"""Command line interface for the compatibility database."""

from __future__ import annotations

import argparse
import json

import torch

from compat_tool.compat import get_op_info
from compat_tool.model_validator import validate_model
from compat_tool.utils import DEFAULT_DB_PATH, load_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="compat", description="Torch-MLIR to TOSA compatibility tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Check a single op")
    check_parser.add_argument("op_name")

    validate_parser = subparsers.add_parser("validate", help="Validate a scripted model")
    validate_parser.add_argument("model_path")

    list_parser = subparsers.add_parser("list", help="List ops from the database")
    group = list_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--supported", action="store_true")
    group.add_argument("--unsupported", action="store_true")

    return parser


def main() -> None:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "check":
        print(json.dumps(get_op_info(args.op_name), indent=2, sort_keys=True))
        return

    if args.command == "validate":
        scripted_model = torch.jit.load(args.model_path)
        print(json.dumps(validate_model(scripted_model), indent=2, sort_keys=True))
        return

    database = load_json(DEFAULT_DB_PATH, default={})
    flag = "supported" if args.supported else "unsupported"
    for op_name in sorted(database):
        if bool(database[op_name].get("supported")) is args.supported:
            print(op_name)


if __name__ == "__main__":
    main()

