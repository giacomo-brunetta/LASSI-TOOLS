"""Standalone GroqFlow measurement worker for a PBS-reserved GroqNode.

This file is staged beside a candidate and executed from the site's ``groqflow``
environment. It intentionally has no imports from :mod:`lassi_x`, because the
GroqFlow environment and the Academy endpoint environment use different Python
minor versions. Correctness is measured against the external C FP64 oracle
staged by the harness; the candidate never receives or reads that oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from groqflow import groqit  # type: ignore[import-not-found]

ARCHITECTURAL_TIMING_EXCLUDES = [
    "allocation",
    "compilation",
    "device_attach",
    "device_to_host",
    "executable_load",
    "host_to_device",
    "queue",
]


def _load_module(path: Path) -> Any:
    """Load a candidate module from a file path.

    Args:
        path: Candidate Python module staged in the PBS workspace.

    Returns:
        Imported module implementing ``build_inputs`` and ``make_model``.

    Raises:
        ImportError: If Python cannot construct a module loader.
        AttributeError: If the candidate omits a required entry point.
    """
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(f"lassi_x_groq_{digest}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load candidate module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for name in ("build_inputs", "make_model"):
        if not hasattr(module, name):
            raise AttributeError(f"candidate does not expose {name}()")
    return module


def _load_oracle(path: Path) -> np.ndarray:
    """Load the harness-generated C FP64 oracle as a flat array.

    Args:
        path: Staged numeric oracle file.

    Returns:
        Flat FP64 NumPy array.
    """
    if path.suffix == ".npy":
        return np.asarray(np.load(path), dtype=np.float64).reshape(-1)
    try:
        values = np.loadtxt(path, delimiter=",", dtype=np.float64)
    except ValueError:
        values = np.loadtxt(path, dtype=np.float64)
    return np.asarray(values, dtype=np.float64).reshape(-1)


def _forward_names(model: torch.nn.Module, count: int) -> list[str]:
    """Resolve the input names GroqFlow uses to trace ``forward``.

    Args:
        model: Candidate model.
        count: Number of positional inputs.

    Returns:
        Forward parameter names, or stable synthetic names as a fallback.
    """
    try:
        parameters = inspect.signature(model.forward).parameters.values()
        names = [
            parameter.name
            for parameter in parameters
            if parameter.name != "self"
            and parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        if len(names) >= count:
            return names[:count]
    except (TypeError, ValueError):
        pass
    return [f"input{index}" for index in range(count)]


def _flatten(output: Any) -> np.ndarray:
    """Convert one GroqFlow output tree to a flat FP64 array.

    Args:
        output: Tensor, NumPy array, or nested tuple/list returned by GroqFlow.

    Returns:
        Concatenated flat FP64 values.
    """
    values = output if isinstance(output, (tuple, list)) else (output,)
    flattened: list[np.ndarray] = []
    for value in values:
        if isinstance(value, (tuple, list)):
            flattened.append(_flatten(value))
        elif hasattr(value, "detach"):
            flattened.append(value.detach().cpu().double().numpy().reshape(-1))
        else:
            flattened.append(np.asarray(value, dtype=np.float64).reshape(-1))
    return np.concatenate(flattened) if flattened else np.asarray([], dtype=np.float64)


def _compare(candidate: np.ndarray, oracle: np.ndarray, rtol: float, atol: float) -> dict[str, Any]:
    """Compute LASSI-X numeric metrics against the external oracle.

    Args:
        candidate: Flat Groq result.
        oracle: Flat C FP64 reference result.
        rtol: Relative equivalence tolerance.
        atol: Absolute equivalence tolerance.

    Returns:
        Equivalence verdict, diagnostic, and error metrics.

    Raises:
        ValueError: If shapes differ or either output contains non-finite values.
    """
    if candidate.shape != oracle.shape:
        raise ValueError(f"shape mismatch: candidate {candidate.shape}, oracle {oracle.shape}")
    if not np.isfinite(candidate).all() or not np.isfinite(oracle).all():
        raise ValueError("candidate or oracle contains NaN or Inf")
    difference = np.abs(candidate - oracle)
    # Match validation.compare_outputs so max_rel_error is comparable across
    # Torch and Groq near reference zeros. This is a tolerance-scaled relative
    # diagnostic, while max_abs_error retains the unscaled error.
    denominator = np.maximum(np.abs(oracle), max(atol, 1e-30))
    max_abs = float(difference.max()) if difference.size else 0.0
    max_rel = float((difference / denominator).max()) if difference.size else 0.0
    oracle_norm = float(np.linalg.norm(oracle))
    relative_l2 = float(np.linalg.norm(candidate - oracle) / max(oracle_norm, 1e-30))
    equivalent = bool(np.allclose(candidate, oracle, rtol=rtol, atol=atol))
    return {
        "equivalent": equivalent,
        "diagnostic": None
        if equivalent
        else {
            "gate": "equivalence",
            "message": "Groq FP16 output differs from the external C FP64 oracle",
            "max_abs_error": max_abs,
            "max_rel_error": max_rel,
        },
        "metrics": {
            "max_abs_error": max_abs,
            "max_rel_error": max_rel,
            "relative_l2": relative_l2,
        },
    }


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write one result record.

    Args:
        path: Final JSON path on the shared filesystem.
        payload: JSON-serializable measurement record.
    """
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def _invoke(model: Any, inputs: dict[str, torch.Tensor]) -> Any:
    """Invoke a GroqModel across supported GroqFlow releases.

    Args:
        model: Compiled GroqModel.
        inputs: Named static inputs used for compilation.

    Returns:
        Runtime output.
    """
    try:
        return model(**inputs)
    except TypeError:
        return model.run(inputs)


def _inputs_for_dataset(module: Any, dataset: str) -> tuple[torch.Tensor, ...]:
    """Build one deterministic candidate input profile.

    Args:
        module: Imported candidate module.
        dataset: Dataset profile requested by the harness.

    Returns:
        Tuple of contiguous FP32 tensors suitable for GroqFlow tracing.
    """
    kwargs: dict[str, Any] = {"device": "cpu", "dtype": torch.float32}
    if "dataset" in inspect.signature(module.build_inputs).parameters:
        kwargs["dataset"] = dataset
    built = module.build_inputs(**kwargs)
    inputs = built if isinstance(built, tuple) else (built,)
    if not inputs or not all(isinstance(value, torch.Tensor) for value in inputs):
        raise TypeError("build_inputs must return a tuple of tensors")
    return tuple(value.float().contiguous() for value in inputs)


def _compile(
    module: Any,
    inputs: tuple[torch.Tensor, ...],
    *,
    build_name: str,
    cache_dir: Path,
) -> tuple[Any, dict[str, torch.Tensor]]:
    """Compile a candidate for one static input profile.

    Args:
        module: Imported candidate module.
        inputs: Static tensors for tracing.
        build_name: GroqFlow cache/build identifier.
        cache_dir: Persistent compilation cache directory.

    Returns:
        Compiled model and its named input mapping.
    """
    network = module.make_model()
    if hasattr(network, "float"):
        network = network.float()
    if hasattr(network, "eval"):
        network = network.eval()
    names = _forward_names(network, len(inputs))
    input_map = dict(zip(names, inputs, strict=False))
    try:
        compiled = groqit(
            network,
            input_map,
            build_name=build_name,
            cache_dir=str(cache_dir),
            rebuild="if_needed",
            monitor=False,
        )
    except TypeError:
        compiled = groqit(
            network,
            input_map,
            build_name=build_name,
            cache_dir=str(cache_dir),
            rebuild="if_needed",
        )
    return compiled, input_map


def main() -> int:
    """Compile, execute, benchmark, and verify one candidate on Groq.

    Returns:
        Process exit code. A structured result is always attempted at ``--output``.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--build-name", required=True)
    parser.add_argument("--dataset", default="default")
    args = parser.parse_args()

    payload: dict[str, Any]
    exit_code = 0
    phase = "load_candidate"
    try:
        module = _load_module(args.module)
        build_name = re.sub(r"[^A-Za-z0-9._-]", "-", args.build_name)[:80]
        phase = "evaluation_compile"
        evaluation_model, evaluation_inputs = _compile(
            module,
            _inputs_for_dataset(module, args.dataset),
            build_name=f"{build_name}-evaluation-{args.dataset}"[:80],
            cache_dir=args.cache_dir,
        )
        benchmark = getattr(evaluation_model, "benchmark", None)
        if not callable(benchmark):
            raise RuntimeError("GroqModel does not expose benchmark(); transport time is not valid")
        phase = "evaluation_warmup"
        for _ in range(args.warmup):
            benchmark(repetitions=1)
        phase = "evaluation_benchmark"
        samples: list[float] = []
        for _ in range(args.iterations):
            # One SDK call per sample is deliberate. Asking the SDK for N
            # repetitions and dividing would measure a throughput loop, not the
            # single graph execution used by the other architectures.
            performance = benchmark(repetitions=1)
            latency = float(getattr(performance, "latency", math.nan))
            if not math.isfinite(latency) or latency <= 0:
                raise RuntimeError("Groq SDK benchmark did not return a finite positive latency")
            samples.append(latency)

        phase = "evaluation_execution"
        candidate = _flatten(_invoke(evaluation_model, evaluation_inputs))
        repeated = _flatten(_invoke(evaluation_model, evaluation_inputs))
        if not np.array_equal(candidate, repeated, equal_nan=True):
            raise RuntimeError("Groq output is nondeterministic across identical evaluation inputs")
        phase = "evaluation_comparison"
        comparison = _compare(candidate, _load_oracle(args.oracle), args.rtol, args.atol)
        payload = {
            "ok": True,
            "valid": True,
            **comparison,
            "median_s": statistics.median(samples),
            "min_s": min(samples),
            "timing": {
                "protocol": "architectural-single-call-v1",
                "scope": "device_resident_graph",
                "source": "groq_sdk_benchmark",
                "clock": "groq_runtime",
                "includes_input_construction": False,
                "cuda_synchronized": False,
                "warmup_count": args.warmup,
                "sample_count": len(samples),
                "invocations_per_sample": 1,
                "samples_s": samples,
                "physical_device_count": 1,
                "input_residency": "device",
                "output_residency_at_stop": "device",
                "excludes": ARCHITECTURAL_TIMING_EXCLUDES,
            },
            "precision": {
                "storage": "fp16",
                "operator": "fp16",
                "accumulator": "groq-backend-defined",
                "output": "fp16",
                "observed_output": "fp16",
                "metadata_source": "backend_contract",
            },
            "source_hash": hashlib.sha256(args.module.read_bytes()).hexdigest(),
            "datasets": {
                "evaluation": args.dataset,
            },
            "evaluation_output": {
                "checked": True,
                "finite": True,
                "numel": int(candidate.size),
                "sha256": hashlib.sha256(np.ascontiguousarray(candidate).tobytes()).hexdigest(),
                "semantic_verified": True,
                "accuracy_source": "same_compiled_model_and_inputs",
            },
        }
    except Exception as exc:
        payload = {
            "ok": False,
            "phase": phase,
            "error": f"{type(exc).__name__}: {exc}",
        }
        exit_code = 1
    _atomic_json(args.output, payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
