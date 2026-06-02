from __future__ import annotations

from pathlib import Path
from typing import Any
import importlib.util
import json
import random
import sys

import numpy as np
import torch

from lassi.analysis.checks import (
    check_mlir_contains_dialect,
    check_mlir_contains_func,
    check_mlir_contains_runtime_args,
    check_mlir_not_constantized,
)


def set_deterministic_seeds(seed: int) -> dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    deterministic_enabled = False
    try:
        torch.use_deterministic_algorithms(True)
        deterministic_enabled = True
    except Exception:
        deterministic_enabled = False

    return {
        "seed": seed,
        "python_random_seeded": True,
        "numpy_seeded": True,
        "torch_seeded": True,
        "torch_deterministic_algorithms": deterministic_enabled,
    }


def build_tensor_from_spec(spec: dict[str, Any]) -> torch.Tensor:
    shape = spec.get("shape")
    if not shape:
        raise ValueError("Tensor spec must include a non-empty 'shape'.")

    dtype_name = spec.get("dtype", "float32")
    device_name = spec.get("device", "cpu")

    dtype_map = {
        "float16": torch.float16,
        "float32": torch.float32,
        "float64": torch.float64,
        "bfloat16": torch.bfloat16,
        "int32": torch.int32,
        "int64": torch.int64,
        "bool": torch.bool,
    }
    if dtype_name not in dtype_map:
        raise ValueError(f"Unsupported dtype in spec: {dtype_name}")

    dtype = dtype_map[dtype_name]

    if "value" in spec:
        value = spec["value"]
        tensor = torch.full(shape, value, dtype=dtype, device=device_name)
    elif dtype in (torch.float16, torch.float32, torch.float64, torch.bfloat16):
        tensor = torch.randn(*shape, dtype=dtype, device=device_name)
    elif dtype in (torch.int32, torch.int64):
        low = spec.get("low", 0)
        high = spec.get("high", 10)
        tensor = torch.randint(low, high, shape, dtype=dtype, device=device_name)
    elif dtype is torch.bool:
        tensor = torch.randint(0, 2, shape, dtype=torch.int64, device=device_name).to(torch.bool)
    else:
        raise ValueError(f"Unsupported dtype in spec: {dtype_name}")

    return tensor


def build_inputs_from_specs(specs: list[dict[str, Any]]) -> tuple[torch.Tensor, ...]:
    return tuple(build_tensor_from_spec(spec) for spec in specs)


def clone_with_perturbation(tensor: torch.Tensor, index: tuple[int, ...], delta: Any) -> torch.Tensor:
    clone = tensor.clone()
    clone[index] = clone[index] + torch.as_tensor(delta, dtype=clone.dtype, device=clone.device)
    return clone


def load_python_module_from_path(path: str | Path, module_name: str | None = None):
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Module file not found: {resolved}")

    module_name = module_name or resolved.stem
    spec = importlib.util.spec_from_file_location(module_name, str(resolved))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for {resolved}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_variants_registry(module: Any, attribute_name: str = "VARIANTS") -> dict[str, Any]:
    variants = getattr(module, attribute_name, None)
    if not isinstance(variants, dict) or not variants:
        raise ValueError(f"Module is missing a non-empty {attribute_name} registry.")
    return variants


def build_variant_by_name(module: Any, name: str, builder_name: str = "build_variant") -> Any:
    builder = getattr(module, builder_name, None)
    if builder is None:
        raise ValueError(f"Module is missing required builder function: {builder_name}")
    return builder(name)


def assert_selected_variant_present(variants: dict[str, Any], name: str) -> None:
    if name not in variants:
        raise KeyError(f"Selected variant '{name}' not found in variant registry: {sorted(variants.keys())}")


def load_toolchain_info(path_or_json: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(path_or_json, dict):
        return path_or_json

    candidate = Path(str(path_or_json))
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    return json.loads(str(path_or_json))


def require_toolchain_feature(info: dict[str, Any], feature: str) -> Any:
    current: Any = info
    for part in feature.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Missing toolchain feature '{feature}'")
        current = current[part]
    return current


def summarize_toolchain_info(info: dict[str, Any]) -> dict[str, Any]:
    return {
        "python_executable": info.get("python", {}).get("executable"),
        "python_version": info.get("python", {}).get("version"),
        "torch_version": info.get("torch", {}).get("version"),
        "torch_mlir_importable": info.get("torch_mlir", {}).get("importable"),
        "torch_mlir_torchscript_compile_available": info.get("torch_mlir", {}).get("torchscript_compile_available"),
        "clang_version": info.get("clang", {}).get("version_probe", {}).get("stdout"),
        "llvm_config_available": info.get("llvm-config", {}).get("available"),
        "mlir_opt_available": info.get("mlir-opt", {}).get("available"),
    }


def classify_verdict(diff_empty: bool, tol_pass: bool) -> str:
    if diff_empty:
        return "IDENTICAL"
    if tol_pass:
        return "ACCEPTABLE_NUMERIC_DRIFT"
    return "DIFF_EXISTS"


def eligible_for_export(verdict: str, sensitivity_pass: bool) -> bool:
    return verdict in {"IDENTICAL", "ACCEPTABLE_NUMERIC_DRIFT"} and sensitivity_pass


def build_variant_result(
    *,
    diff_empty: bool,
    diff_file: str | Path,
    tolerance_applied: bool,
    tolerance_pass: bool,
    rtol: float,
    atol: float,
    max_abs_err_vs_oracle: float,
    max_rel_err_vs_oracle: float,
    input_sensitivity_max_abs_diff: float,
    input_sensitivity_pass: bool,
    candidate_output_normalized: str | Path | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verdict = classify_verdict(diff_empty, tolerance_pass)
    result = {
        "diff_empty": diff_empty,
        "diff_file": str(Path(diff_file).resolve()),
        "tolerance_applied": tolerance_applied,
        "tolerance_pass": tolerance_pass,
        "rtol": rtol,
        "atol": atol,
        "max_abs_err_vs_oracle": max_abs_err_vs_oracle,
        "max_rel_err_vs_oracle": max_rel_err_vs_oracle,
        "input_sensitivity_max_abs_diff": input_sensitivity_max_abs_diff,
        "input_sensitivity_pass": input_sensitivity_pass,
        "verdict": verdict,
        "eligible_for_export_profiling": eligible_for_export(verdict, input_sensitivity_pass),
        "candidate_output_normalized": str(Path(candidate_output_normalized).resolve()) if candidate_output_normalized else None,
    }
    if extras:
        result.update(extras)
    return result


def build_verification_summary(
    *,
    seed: int,
    golden_output: str | Path,
    variant_results: dict[str, dict[str, Any]],
    warning_lines: list[dict[str, str]] | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verdicts = [item["verdict"] for item in variant_results.values()]
    if any(verdict == "DIFF_EXISTS" for verdict in verdicts):
        final_classification = "DIFF_EXISTS"
    elif any(verdict == "ACCEPTABLE_NUMERIC_DRIFT" for verdict in verdicts):
        final_classification = "ACCEPTABLE_NUMERIC_DRIFT"
    else:
        final_classification = "IDENTICAL"

    summary = {
        "seed": seed,
        "golden_output": str(Path(golden_output).resolve()),
        "variant_results": variant_results,
        "warning_lines": warning_lines or [],
        "final_classification": final_classification,
    }
    if extras:
        summary.update(extras)
    return summary


def write_json_report(path: str | Path, obj: dict[str, Any]) -> Path:
    resolved = Path(path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    return resolved


def default_pt_output_path(model_file: str | Path) -> Path:
    return Path(model_file).resolve().with_suffix(".pt")


def default_mlir_output_path(pt_path: str | Path, target: str = "tosa") -> Path:
    resolved = Path(pt_path).resolve()
    if target == "tosa":
        return resolved.with_suffix(".mlir")
    return resolved.with_name(f"{resolved.stem}_{target}.mlir")


def artifact_paths_for_variant(base_dir: str | Path, variant_name: str) -> dict[str, Path]:
    base = Path(base_dir).resolve()
    return {
        "pt": base / f"{variant_name}.pt",
        "mlir": base / f"{variant_name}.mlir",
        "normalized_output": base / f"{variant_name}_output_normalized.txt",
        "npy_output": base / f"{variant_name}_output.npy",
        "diff": base / f"diff_{variant_name}.txt",
    }


def load_mlir_text(path: str | Path) -> str:
    return Path(path).resolve().read_text(encoding="utf-8", errors="ignore")


def extract_mlir_function_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    lines = text.splitlines()
    buffer: list[str] = []
    depth = 0
    in_func = False

    for line in lines:
        if line.strip().startswith("func.func @"):
            in_func = True
            depth = line.count("{") - line.count("}")
            buffer = [line]
            continue

        if in_func:
            buffer.append(line)
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                bodies.append("\n".join(buffer))
                in_func = False
                buffer = []

    return bodies


def count_nonconstant_ops(text: str) -> int:
    count = 0
    for body in extract_mlir_function_bodies(text):
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("func.func @") or stripped == "}":
                continue
            if '"tosa.const"' in stripped or stripped.startswith("return "):
                continue
            if "=" in stripped or stripped.startswith('"'):
                count += 1
    return count


def summarize_mlir_checks(path: str | Path, dialect: str = "tosa.") -> dict[str, Any]:
    resolved = Path(path).resolve()
    return {
        "path": str(resolved),
        "contains_func": check_mlir_contains_func(resolved)["contains_func"],
        "contains_runtime_args": check_mlir_contains_runtime_args(resolved)["contains_runtime_args"],
        "contains_dialect": check_mlir_contains_dialect(resolved, dialect=dialect)["contains_dialect"],
        "not_constantized": check_mlir_not_constantized(resolved)["not_constantized"],
        "nonconstant_ops_in_func_body": count_nonconstant_ops(load_mlir_text(resolved)),
    }
