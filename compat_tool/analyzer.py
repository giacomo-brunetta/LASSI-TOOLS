"""Compatibility analysis by attempting Torch-MLIR TOSA lowering."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from typing import Any

import torch

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - dependency optional at runtime
    def tqdm(iterable, **_: Any):
        """Fallback iterator when tqdm is unavailable."""
        return iterable

from compat_tool.utils import (
    DATA_DIR,
    DEFAULT_COMPATIBILITY_PATH,
    build_attempt_profiles,
    build_bound_invocation,
    load_json,
    load_all_ops,
    normalize_error,
    save_json,
    time_limit,
)


LOGGER = logging.getLogger(__name__)
LOWERING_ERROR_MARKERS = (
    "failed to legalize operation",
    "unsupported by backend lowering",
)
DEFAULT_TIMEOUT_SECONDS = 30
KNOWN_UNSAFE_OPS = {
    "aten.batch_norm",
}
RISKY_ANALYSIS_PATH = DATA_DIR / "unsupported_analysis.json"


def _load_risky_ops() -> set[str]:
    """Load ops that should be isolated in a subprocess."""
    try:
        analysis = load_json(RISKY_ANALYSIS_PATH, default={})
        unsupported = analysis.get("unsupported_ops", {})
    except Exception:
        unsupported = {}
    risky = {
        op_name
        for op_name, info in unsupported.items()
        if info.get("category") in {"manual_review", "harness_wrong_inputs_or_dtype"}
    }
    risky.update(KNOWN_UNSAFE_OPS)
    return risky


def _resolve_torch_mlir_api() -> tuple[Any, Any]:
    """Resolve the installed torch-mlir compile entrypoint and OutputType enum."""
    import torch_mlir  # type: ignore

    compile_fn = getattr(torch_mlir, "compile", None)
    output_type = getattr(torch_mlir, "OutputType", None)
    if compile_fn is not None and output_type is not None:
        return compile_fn, output_type

    from torch_mlir import torchscript  # type: ignore

    return torchscript.compile, torchscript.OutputType


def _run_attempt(
    op_name: str,
    op_meta: dict[str, Any],
    profile: dict[str, Any],
    compile_fn: Any,
    output_type: Any,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run a single compile attempt for one op/profile pair."""
    invocation, example_inputs, input_spec = build_bound_invocation(
        op_name,
        op_meta,
        tensor_dtype=profile["tensor_dtype"],
        tensor_mode=profile["tensor_mode"],
    )

    with time_limit(timeout_seconds):
        module = invocation.build_module()
        scripted = torch.jit.trace(module, example_inputs, strict=False, check_trace=False)
        compile_fn(
            scripted,
            example_inputs,
            output_type=output_type.TOSA,
        )

    return {
        "supported": True,
        "error": None,
        "dtype": str(profile["tensor_dtype"]).replace("torch.", ""),
        "range_note": profile.get("range_note"),
        "input_spec": input_spec,
    }


def _run_attempt_subprocess(
    op_name: str,
    profile: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run one attempt in a subprocess so native crashes do not kill the full sweep."""
    payload = {
        "op_name": op_name,
        "profile_name": profile["name"],
        "tensor_dtype": str(profile["tensor_dtype"]).replace("torch.", ""),
        "tensor_mode": profile["tensor_mode"],
        "range_note": profile.get("range_note"),
        "timeout_seconds": timeout_seconds,
    }
    script = r"""
import json
import sys
import torch
from compat_tool.analyzer import _resolve_torch_mlir_api, _run_attempt
from compat_tool.utils import load_all_ops

payload = json.loads(sys.argv[1])
dtype = getattr(torch, payload["tensor_dtype"])
profile = {
    "name": payload["profile_name"],
    "tensor_dtype": dtype,
    "tensor_mode": payload["tensor_mode"],
    "range_note": payload.get("range_note"),
}
compile_fn, output_type = _resolve_torch_mlir_api()
op_meta = load_all_ops().get(payload["op_name"], {})
result = _run_attempt(
    payload["op_name"],
    op_meta,
    profile,
    compile_fn,
    output_type,
    payload["timeout_seconds"],
)
print(json.dumps(result))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 5,
    )
    if completed.returncode == 0:
        stdout = completed.stdout.strip().splitlines()
        if not stdout:
            raise RuntimeError("Empty subprocess output")
        return json.loads(stdout[-1])

    stderr = (completed.stderr or completed.stdout).strip()
    if not stderr:
        stderr = f"Subprocess exited with code {completed.returncode}"
    return {
        "supported": False,
        "error": f"Subprocess failure (exit {completed.returncode}): {stderr}",
        "dtype": payload["tensor_dtype"],
        "range_note": payload.get("range_note"),
        "input_spec": "Unavailable due to subprocess failure",
    }


def test_op(
    op_name: str,
    op_meta: dict[str, Any] | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """
    Test whether a single op lowers to TOSA.

    Success is defined only by a successful `torch_mlir.compile(..., output_type=TOSA)`.
    """
    try:
        _resolve_torch_mlir_api()
    except Exception as error:  # pragma: no cover - environment dependent
        return {
            "supported": False,
            "error": f"torch-mlir unavailable: {normalize_error(error)}",
            "attempts": {},
            "supported_profiles": [],
            "range_restriction": None,
            "dtype_notes": [],
        }

    if op_meta is None:
        op_meta = load_all_ops().get(op_name, {})

    if op_name in KNOWN_UNSAFE_OPS:
        return {
            "supported": False,
            "error": "Skipped automatic probe because this op crashes the current runtime with schema-appropriate test inputs.",
            "attempts": {},
            "supported_profiles": [],
            "range_restriction": None,
            "dtype_notes": [],
        }

    attempts: dict[str, dict[str, Any]] = {}
    supported_profiles: list[str] = []
    range_restriction: str | None = None
    risky_ops = _load_risky_ops()
    compile_context: tuple[Any, Any] | None = None

    for profile in build_attempt_profiles(op_name):
        if profile.get("range_note") and profile.get("tensor_mode") != "default":
            range_restriction = profile["range_note"]
        try:
            if op_name in risky_ops:
                attempts[profile["name"]] = _run_attempt_subprocess(op_name, profile, timeout_seconds)
            else:
                if compile_context is None:
                    compile_context = _resolve_torch_mlir_api()
                compile_fn, output_type = compile_context
                attempts[profile["name"]] = _run_attempt(
                    op_name,
                    op_meta,
                    profile,
                    compile_fn,
                    output_type,
                    timeout_seconds,
                )
            if attempts[profile["name"]].get("supported"):
                supported_profiles.append(profile["name"])
        except Exception as error:
            message = normalize_error(error)
            attempts[profile["name"]] = {
                "supported": False,
                "error": message,
                "dtype": str(profile["tensor_dtype"]).replace("torch.", ""),
                "range_note": profile.get("range_note"),
                "input_spec": "Unavailable due to analyzer exception",
            }
            lowered_message = message.lower()
            if not any(marker in lowered_message for marker in LOWERING_ERROR_MARKERS):
                LOGGER.debug("Op %s failed for profile %s: %s", op_name, profile["name"], message)

    primary_error = None
    for profile_name in ("float32_default", "float32_domain_(0,inf)", "float32_probability_[0,1]", "int32_default"):
        attempt = attempts.get(profile_name)
        if attempt and attempt.get("error"):
            primary_error = attempt["error"]
            break
    if primary_error is None:
        for attempt in attempts.values():
            if attempt.get("error"):
                primary_error = attempt["error"]
                break

    dtype_notes: list[str] = []
    float_attempt = attempts.get("float32_default")
    int_attempt = attempts.get("int32_default")
    if float_attempt and int_attempt:
        if not float_attempt.get("supported") and int_attempt.get("supported"):
            dtype_notes.append("Supported with int32 retry, but not with the default float32 inputs.")
        elif float_attempt.get("supported") and not int_attempt.get("supported"):
            dtype_notes.append("Supported with float32 inputs, but the int32 retry failed.")

    return {
        "supported": bool(supported_profiles),
        "error": None if supported_profiles else primary_error,
        "attempts": attempts,
        "supported_profiles": supported_profiles,
        "range_restriction": range_restriction,
        "dtype_notes": dtype_notes,
    }


def analyze_all_ops(
    ops: dict[str, Any],
    output_path: str = str(DEFAULT_COMPATIBILITY_PATH),
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, dict[str, Any]]:
    """Analyze every op, reusing cached results already written to disk."""
    results: dict[str, dict[str, Any]] = load_json(output_path, default={})

    for op_name in tqdm(sorted(ops), desc="Analyzing ops"):
        cached = results.get(op_name)
        if (
            cached
            and "attempts" in cached
            and "supported_profiles" in cached
            and "range_restriction" in cached
            and "dtype_notes" in cached
        ):
            continue
        results[op_name] = test_op(op_name, op_meta=ops.get(op_name), timeout_seconds=timeout_seconds)
        save_json(output_path, results)

    return results
