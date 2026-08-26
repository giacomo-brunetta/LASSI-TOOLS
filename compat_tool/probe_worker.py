"""Isolated worker for one compatibility compile cell."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, cast

from compat_tool.checker_base import CheckerUnavailableError
from compat_tool.fixtures import build_case
from compat_tool.io import load_json, stable_hash
from compat_tool.target import checker_class, load_target


def _metadata(target: dict[str, Any]) -> dict[str, Any]:
    checker = checker_class(target)(target)
    return cast("dict[str, Any]", checker.metadata())


def _probe(
    target: dict[str, Any],
    manifest: dict[str, Any],
    op_name: str,
    precision: str,
    case_name: str,
    work_dir: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    case = manifest["operators"][op_name]["cases"][precision][case_name]
    recipe = case["recipe"]
    target_identity = {key: value for key, value in target.items() if key != "config_path"}
    case_hash = stable_hash(
        {
            "manifest_hash": manifest["manifest_hash"],
            "target": target_identity,
            "op": op_name,
            "precision": precision,
            "case": case,
        }
    )
    try:
        module, inputs, input_spec = build_case(
            op_name,
            manifest["operators"][op_name]["metadata"],
            recipe,
        )
    except Exception as error:
        return {
            "status": "schema_mismatch",
            "error": f"{type(error).__name__}: {error}",
            "duration_s": time.monotonic() - started,
            "cache_key": case_hash,
        }

    try:
        checker = checker_class(target)(target)
        result = cast(
            "dict[str, Any]",
            checker.compile(
                module,
                inputs,
                op_name=op_name,
                precision=precision,
                case_hash=case_hash,
                work_dir=work_dir,
            ),
        )
        result.setdefault("status", "compiled")
        result.update(
            {
                "input_spec": input_spec,
                "duration_s": time.monotonic() - started,
                "cache_key": case_hash,
            }
        )
        return result
    except CheckerUnavailableError as error:
        return {
            "status": "environment_error",
            "error": f"{type(error).__name__}: {error}",
            "input_spec": input_spec,
            "duration_s": time.monotonic() - started,
            "cache_key": case_hash,
        }
    except Exception as error:
        return {
            "status": "compile_rejected",
            "error": f"{type(error).__name__}: {error}",
            "input_spec": input_spec,
            "duration_s": time.monotonic() - started,
            "cache_key": case_hash,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--op")
    parser.add_argument("--precision")
    parser.add_argument("--case", default="canonical")
    parser.add_argument("--work-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        target = load_target(args.target)
        if args.metadata:
            payload = {"ok": True, "metadata": _metadata(target)}
        else:
            if args.manifest is None or args.op is None or args.precision is None:
                raise ValueError("probe mode requires --manifest, --op, and --precision")
            manifest = load_json(args.manifest)
            payload = {
                "ok": True,
                "result": _probe(
                    target,
                    manifest,
                    args.op,
                    args.precision,
                    args.case,
                    args.work_dir,
                ),
            }
        print(json.dumps(payload, allow_nan=False))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
