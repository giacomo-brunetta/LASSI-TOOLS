from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import statistics
import time
from pathlib import Path
from typing import cast

import numpy as np
import torch

from .runner import PRECISIONS, load_module
from .validation import compare_outputs, load_reference_output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--precision", choices=sorted(PRECISIONS), required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--dataset", default="default")
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--require-equivalence", action="store_true")
    parser.add_argument("--invariant")
    parser.add_argument("--invariant-threshold", type=float)
    args = parser.parse_args()
    phase = "load_candidate"
    try:
        torch.manual_seed(args.seed)
        module = load_module(args.module)
        dtype = PRECISIONS[args.precision]
        kwargs = {"device": args.device, "dtype": dtype}
        if args.fixture and "fixture" in inspect.signature(module.build_inputs).parameters:
            kwargs["fixture"] = args.fixture

        def build_inputs(dataset: str) -> tuple[torch.Tensor, ...]:
            selected = dict(kwargs)
            if "dataset" in inspect.signature(module.build_inputs).parameters:
                selected["dataset"] = dataset
            built = module.build_inputs(**selected)
            if not isinstance(built, tuple):
                raise TypeError("build_inputs must return a tuple")
            return cast("tuple[torch.Tensor, ...]", built)

        def build_model() -> torch.nn.Module:
            built = module.make_model()
            if hasattr(built, "eval"):
                built.eval()
            if hasattr(built, "to"):
                built.to(args.device)
            return cast("torch.nn.Module", built)

        def flatten(output: object) -> tuple[np.ndarray, tuple[torch.Tensor, ...]]:
            values = output if isinstance(output, tuple) else (output,)
            if not values or not all(isinstance(value, torch.Tensor) for value in values):
                raise TypeError("forward must return a tensor or tuple of tensors")
            tensors = tuple(values)
            flat_output = np.concatenate(
                [value.detach().double().cpu().numpy().reshape(-1) for value in tensors]
            )
            return flat_output, tensors

        phase = "evaluation_setup"
        model = build_model()
        cuda = args.device.startswith("cuda")
        with torch.no_grad():
            torch.manual_seed(args.seed)
            inputs = build_inputs(args.dataset)
            phase = "evaluation_warmup"
            for _ in range(args.warmup):
                model(*inputs)
            if cuda:
                torch.cuda.synchronize()
            phase = "evaluation_benchmark"
            samples = []
            timed_output: object | None = None
            for _ in range(args.iterations):
                if cuda:
                    torch.cuda.synchronize()
                start = time.perf_counter()
                timed_output = model(*inputs)
                if cuda:
                    torch.cuda.synchronize()
                samples.append(time.perf_counter() - start)
            assert timed_output is not None
            flat, tensors = flatten(timed_output)
            repeated, _ = flatten(model(*inputs))
            if not np.array_equal(flat, repeated, equal_nan=True):
                raise RuntimeError(
                    "candidate is stateful or nondeterministic across identical evaluation inputs"
                )
        phase = "evaluation_comparison"
        oracle = load_reference_output(args.oracle)
        ok, diagnostic, metrics = compare_outputs(
            flat,
            oracle,
            rtol=args.rtol,
            atol=args.atol,
            max_mismatches=20,
        )
        valid = ok or (
            not args.require_equivalence
            and diagnostic is not None
            and diagnostic.gate == "equivalence"
        )
        precision = getattr(module, "LASSI_PRECISION", {}) or {}
        output_dtype = str(tensors[0].dtype).removeprefix("torch.")
        invariant_error = None
        invariant_candidate = {}
        if args.invariant:
            module_name, separator, attribute = args.invariant.partition(":")
            if not separator:
                raise ValueError("invariant must use module:function syntax")
            function = getattr(importlib.import_module(module_name), attribute)
            invariant_result = function(flat, oracle)
            if isinstance(invariant_result, dict):
                invariant_candidate = invariant_result
                invariant_error = float(invariant_result["error"])
            else:
                invariant_error = float(invariant_result)
                invariant_candidate = {"error": invariant_error}
            if args.invariant_threshold is not None and invariant_error > args.invariant_threshold:
                valid = False
        payload = {
            "ok": True,
            "valid": valid,
            "equivalent": ok,
            "diagnostic": diagnostic.to_dict() if diagnostic else None,
            "median_s": statistics.median(samples),
            "min_s": min(samples),
            "timing": {
                "scope": "model_forward",
                "source": "remote_measure_worker",
                "clock": "time.perf_counter",
                "includes_input_construction": False,
                "cuda_synchronized": cuda,
            },
            "metrics": metrics,
            "invariant_error": invariant_error,
            "invariant_candidate": invariant_candidate,
            "precision": {
                "storage": precision.get("storage", args.precision),
                "operator": precision.get("operator", args.precision),
                "accumulator": precision.get("accumulator", args.precision),
                "output": precision.get("output", output_dtype),
                "observed_output": output_dtype,
                "metadata_source": "candidate_declared" if precision else "inferred",
            },
            "source_hash": hashlib.sha256(args.module.read_bytes()).hexdigest(),
            "datasets": {
                "evaluation": args.dataset,
            },
            "evaluation_output": {
                "checked": True,
                "finite": bool(np.isfinite(flat).all()),
                "numel": int(flat.size),
                "sha256": hashlib.sha256(np.ascontiguousarray(flat).tobytes()).hexdigest(),
                "semantic_verified": True,
                "accuracy_source": "timed_iteration",
            },
        }
        print(json.dumps(payload))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "phase": phase,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
