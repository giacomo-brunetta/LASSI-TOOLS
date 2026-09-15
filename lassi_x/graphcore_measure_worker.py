"""Standalone architectural-latency worker for one Graphcore IPU.

The harness stages this file because PopTorch installations commonly use a
Python version different from the harness. Keep it independent of ``lassi_x``.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import inspect
import json
import os
import statistics
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import popart  # type: ignore[import-not-found]
import torch

PRECISIONS = {
    "fp32": torch.float32,
    "fp16": torch.float16,
}
TIMING_EXCLUDES = [
    "allocation",
    "compilation",
    "device_attach",
    "device_to_host",
    "executable_load",
    "host_to_device",
    "queue",
]


def _load_module(path: Path) -> Any:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(f"lassi_x_ipu_{digest}", path)
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
    if path.suffix == ".npy":
        return np.asarray(np.load(path), dtype=np.float64).reshape(-1)
    try:
        values = np.loadtxt(path, delimiter=",", dtype=np.float64)
    except ValueError:
        values = np.loadtxt(path, dtype=np.float64)
    return np.asarray(values, dtype=np.float64).reshape(-1)


def _flatten(output: Any) -> np.ndarray:
    values = output if isinstance(output, (tuple, list)) else (output,)
    flattened = []
    for value in values:
        if isinstance(value, (tuple, list)):
            flattened.append(_flatten(value))
        elif hasattr(value, "detach"):
            flattened.append(value.detach().cpu().double().numpy().reshape(-1))
        else:
            flattened.append(np.asarray(value, dtype=np.float64).reshape(-1))
    return np.concatenate(flattened) if flattened else np.asarray([], dtype=np.float64)


def _compare(candidate: np.ndarray, oracle: np.ndarray, rtol: float, atol: float) -> dict[str, Any]:
    if candidate.shape != oracle.shape:
        raise ValueError(f"shape mismatch: candidate {candidate.shape}, oracle {oracle.shape}")
    if not np.isfinite(candidate).all() or not np.isfinite(oracle).all():
        raise ValueError("candidate or oracle contains NaN or Inf")
    difference = np.abs(candidate - oracle)
    denominator = np.maximum(np.abs(oracle), max(atol, 1e-30))
    max_abs = float(difference.max()) if difference.size else 0.0
    max_rel = float((difference / denominator).max()) if difference.size else 0.0
    relative_l2 = float(
        np.linalg.norm(candidate - oracle) / max(float(np.linalg.norm(oracle)), 1e-30)
    )
    equivalent = bool(np.allclose(candidate, oracle, rtol=rtol, atol=atol))
    return {
        "equivalent": equivalent,
        "diagnostic": None
        if equivalent
        else {
            "gate": "equivalence",
            "message": "Graphcore output differs from the external C FP64 oracle",
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
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def _build_inputs(module: Any, args: argparse.Namespace, dtype: torch.dtype) -> tuple[Any, ...]:
    kwargs: dict[str, Any] = {"device": "cpu", "dtype": dtype}
    signature = inspect.signature(module.build_inputs)
    if args.fixture and "fixture" in signature.parameters:
        kwargs["fixture"] = args.fixture
    if "dataset" in signature.parameters:
        kwargs["dataset"] = args.dataset
    built = module.build_inputs(**kwargs)
    values = built if isinstance(built, tuple) else (built,)
    if not values or not all(isinstance(value, torch.Tensor) for value in values):
        raise TypeError("build_inputs must return a tuple of tensors")
    return tuple(value.to(dtype=dtype).contiguous() for value in values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--architecture", choices=["graphcore_ipu"], required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--precision", choices=sorted(PRECISIONS), required=True)
    parser.add_argument("--dataset", default="default")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--clock-hz",
        type=float,
        default=1_850_000_000.0,
        help="IPU tile clock used to convert PopART hardware cycles to seconds.",
    )
    parser.add_argument("--require-equivalence", action="store_true")
    args = parser.parse_args()

    payload: dict[str, Any]
    phase = "load_candidate"
    device = None
    exit_code = 0
    try:
        torch.manual_seed(args.seed)
        module = _load_module(args.module)
        dtype = PRECISIONS[args.precision]
        inputs = _build_inputs(module, args, dtype)
        model = module.make_model()
        if hasattr(model, "eval"):
            model.eval()
        if hasattr(model, "to"):
            model.to(dtype=dtype)

        if not np.isfinite(args.clock_hz) or args.clock_hz <= 0:
            raise ValueError("--clock-hz must be finite and positive")

        # PopTorch's getComputeLatency() is zero on this site's runtime even
        # when a graph has demonstrably executed.  Export once to ONNX and use
        # PopART's documented hardware cycle counter instead.  This is an IPU
        # clock counter, not a host-wall-clock measurement.
        phase = "evaluation_export"
        model_bytes = BytesIO()
        # ONNX output names must identify tensors, not flattened elements.
        probe_output = model(*inputs)
        output_tensors = (
            probe_output if isinstance(probe_output, (tuple, list)) else (probe_output,)
        )
        output_names = [f"output_{index}" for index in range(len(output_tensors))]
        input_names = [f"input_{index}" for index in range(len(inputs))]
        torch.onnx.export(
            model,
            inputs,
            model_bytes,
            input_names=input_names,
            output_names=output_names,
            # PopART 3.3 supports ONNX operators through opset 11.
            opset_version=11,
            do_constant_folding=True,
        )

        phase = "evaluation_compile"
        options = popart.SessionOptions()
        options.instrumentWithHardwareCycleCounter = True
        options.hardwareInstrumentations = {popart.Instrumentation.Outer}
        anchors = {name: popart.AnchorReturnType("ALL") for name in output_names}
        device = popart.DeviceManager().acquireAvailableDevice(1)
        if device is None:
            raise RuntimeError("PopART could not acquire one IPU")
        executable = popart.InferenceSession(
            fnModel=model_bytes.getvalue(),
            dataFlow=popart.DataFlow(1, anchors),
            userOptions=options,
            deviceInfo=device,
        )
        executable.prepareDevice()
        anchor_arrays = executable.initAnchorArrays()
        stepio = popart.PyStepIO(
            {
                name: value.detach().cpu().numpy()
                # The remote PopART interpreter is Python 3.8, predating
                # zip(strict=True); input_names is built from inputs above.
                for name, value in zip(input_names, inputs)  # noqa: B905
            },
            anchor_arrays,
        )

        phase = "evaluation_warmup"
        for _ in range(args.warmup):
            executable.run(stepio)

        phase = "evaluation_benchmark"
        samples = []
        timed_output = None
        for _ in range(args.iterations):
            executable.run(stepio)
            cycles = float(executable.getCycleCount())
            elapsed_s = cycles / args.clock_hz
            if not np.isfinite(elapsed_s) or elapsed_s <= 0:
                raise RuntimeError("PopART did not return a finite positive hardware cycle count")
            samples.append(elapsed_s)
            timed_output = tuple(
                torch.from_numpy(anchor_arrays[name].copy()) for name in output_names
            )
        if timed_output is None:
            raise RuntimeError("no timed invocation was executed")

        candidate = _flatten(timed_output)
        executable.run(stepio)
        repeated = _flatten(
            tuple(torch.from_numpy(anchor_arrays[name].copy()) for name in output_names)
        )
        if not np.array_equal(candidate, repeated, equal_nan=True):
            raise RuntimeError("IPU output is nondeterministic across identical evaluation inputs")
        phase = "evaluation_comparison"
        comparison = _compare(candidate, _load_oracle(args.oracle), args.rtol, args.atol)
        equivalent = bool(comparison["equivalent"])
        valid = equivalent or not args.require_equivalence
        declared = getattr(module, "LASSI_PRECISION", {}) or {}
        observed = str(getattr(timed_output[0], "dtype", dtype))
        if observed.startswith("torch."):
            observed = observed[len("torch.") :]
        payload = {
            "ok": True,
            "valid": valid,
            **comparison,
            "median_s": statistics.median(samples),
            "min_s": min(samples),
            "timing": {
                "protocol": "architectural-single-call-v1",
                "scope": "device_resident_graph",
                "source": "popart_get_cycle_count",
                "clock": "ipu_hardware_cycle_counter",
                "includes_input_construction": False,
                "cuda_synchronized": False,
                "warmup_count": args.warmup,
                "sample_count": len(samples),
                "invocations_per_sample": 1,
                "samples_s": samples,
                "physical_device_count": 1,
                "input_residency": "device",
                "output_residency_at_stop": "device",
                "excludes": TIMING_EXCLUDES,
            },
            "precision": {
                "storage": declared.get("storage", args.precision),
                "operator": declared.get("operator", args.precision),
                "accumulator": declared.get("accumulator", args.precision),
                "output": declared.get("output", observed),
                "observed_output": observed,
                "metadata_source": "candidate_declared" if declared else "inferred",
            },
            "source_hash": hashlib.sha256(args.module.read_bytes()).hexdigest(),
            "datasets": {"evaluation": args.dataset},
            "evaluation_output": {
                "checked": True,
                "finite": bool(np.isfinite(candidate).all()),
                "numel": int(candidate.size),
                "sha256": hashlib.sha256(np.ascontiguousarray(candidate).tobytes()).hexdigest(),
                "semantic_verified": True,
                "accuracy_source": "timed_ipu_invocation",
            },
        }
    except Exception as exc:
        payload = {"ok": False, "phase": phase, "error": f"{type(exc).__name__}: {exc}"}
        exit_code = 1
    finally:
        if device is not None:
            # Teardown is outside both the metric and its validity. Preserve
            # the completed record even if the SDK cannot release cleanly.
            with contextlib.suppress(Exception):
                device.detach()
    _atomic_json(args.output, payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
