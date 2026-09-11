"""Whole-model compiler qualification worker used on local or remote resources."""

from __future__ import annotations

import argparse
import importlib.resources
import inspect
import json
from pathlib import Path
from typing import Any

from .compat.checkers.base import CheckerUnavailableError
from .compat.target import checker_class, load_target
from .runner import PRECISIONS, load_module


def _target_path(target_id: str) -> Path:
    root = importlib.resources.files("lassi_x.compat").joinpath("targets", target_id)
    return Path(str(root.joinpath("target.yaml")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--precision", choices=sorted(PRECISIONS), required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--dataset", default="default")
    args = parser.parse_args()
    try:
        candidate = load_module(args.module)
        kwargs: dict[str, Any] = {"device": "cpu", "dtype": PRECISIONS[args.precision]}
        if args.fixture and "fixture" in inspect.signature(candidate.build_inputs).parameters:
            kwargs["fixture"] = args.fixture
        if "dataset" in inspect.signature(candidate.build_inputs).parameters:
            kwargs["dataset"] = args.dataset
        inputs = candidate.build_inputs(**kwargs)
        if not isinstance(inputs, tuple):
            raise TypeError("build_inputs must return a tuple")
        module = candidate.make_model().eval()
        target = load_target(_target_path(args.target))
        checker = checker_class(target)(target)
        result = checker.compile(
            module,
            inputs,
            op_name=f"whole-model:{args.module.name}",
            precision=args.precision,
            case_hash="whole-model",
            work_dir=Path.cwd(),
        )
        print(json.dumps({"ok": True, "status": "compiled", "result": result}, default=str))
        return 0
    except CheckerUnavailableError as exc:
        print(json.dumps({"ok": False, "status": "unavailable", "error": str(exc)}))
        return 2
    except Exception as exc:
        print(
            json.dumps({"ok": False, "status": "rejected", "error": f"{type(exc).__name__}: {exc}"})
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
