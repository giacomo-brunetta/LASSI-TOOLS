from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence
import json
import re
import subprocess

import numpy as np


FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")


def _as_path(path: str | Path) -> Path:
    return path if isinstance(path, Path) else Path(path)


def assert_file_exists(path: str | Path) -> Path:
    resolved = _as_path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Required file not found: {resolved}")
    return resolved


def assert_nonempty_file(path: str | Path) -> Path:
    resolved = assert_file_exists(path)
    if resolved.stat().st_size == 0:
        raise ValueError(f"Required file is empty: {resolved}")
    return resolved


def assert_paths_exist(paths: Iterable[str | Path]) -> list[Path]:
    return [assert_file_exists(path) for path in paths]


def assert_json_serializable(obj: Any) -> None:
    json.dumps(obj)


def check_pt_artifact(path: str | Path) -> dict[str, Any]:
    resolved = assert_nonempty_file(path)
    return {
        "path": str(resolved),
        "exists": True,
        "nonempty": True,
        "size_bytes": resolved.stat().st_size,
    }


def check_mlir_artifact_exists(path: str | Path) -> dict[str, Any]:
    resolved = assert_file_exists(path)
    return {
        "path": str(resolved),
        "exists": True,
    }


def check_mlir_nonempty(path: str | Path) -> dict[str, Any]:
    resolved = assert_nonempty_file(path)
    return {
        "path": str(resolved),
        "nonempty": True,
        "size_bytes": resolved.stat().st_size,
    }


def _read_text(path: str | Path) -> str:
    resolved = assert_nonempty_file(path)
    return resolved.read_text(encoding="utf-8", errors="ignore")


def check_mlir_contains_func(path: str | Path) -> dict[str, Any]:
    text = _read_text(path)
    found = "func.func @" in text
    return {
        "path": str(_as_path(path).resolve()),
        "contains_func": found,
    }


def check_mlir_contains_runtime_args(path: str | Path) -> dict[str, Any]:
    text = _read_text(path)
    found = bool(re.search(r"%arg\d+", text))
    return {
        "path": str(_as_path(path).resolve()),
        "contains_runtime_args": found,
    }


def check_mlir_not_constantized(path: str | Path) -> dict[str, Any]:
    text = _read_text(path)
    lines = [line.strip() for line in text.splitlines()]
    in_func = False
    nonconstant_ops = 0

    for line in lines:
        if line.startswith("func.func @"):
            in_func = True
            continue
        if in_func and line == "}":
            in_func = False
            continue
        if not in_func:
            continue
        if '"tosa.const"' in line or line.startswith("return ") or line == "return":
            continue
        if "=" in line or line.startswith('"'):
            nonconstant_ops += 1

    return {
        "path": str(_as_path(path).resolve()),
        "nonconstant_ops_in_func_body": nonconstant_ops,
        "not_constantized": nonconstant_ops > 0,
    }


def check_mlir_contains_dialect(path: str | Path, dialect: str = "tosa.") -> dict[str, Any]:
    text = _read_text(path)
    found = dialect in text
    return {
        "path": str(_as_path(path).resolve()),
        "dialect": dialect,
        "contains_dialect": found,
    }


def check_artifact_pair(pt_path: str | Path, mlir_path: str | Path) -> dict[str, Any]:
    return {
        "pt": check_pt_artifact(pt_path),
        "mlir_exists": check_mlir_artifact_exists(mlir_path),
        "mlir_nonempty": check_mlir_nonempty(mlir_path),
    }


def _to_numpy(array_like: Any) -> np.ndarray:
    if isinstance(array_like, np.ndarray):
        return array_like
    return np.asarray(array_like)


def compare_arrays_exact(a: Any, b: Any) -> bool:
    return bool(np.array_equal(_to_numpy(a), _to_numpy(b)))


def compare_arrays_close(a: Any, b: Any, rtol: float = 1e-6, atol: float = 1e-6) -> bool:
    return bool(np.allclose(_to_numpy(a), _to_numpy(b), rtol=rtol, atol=atol))


def max_abs_error(a: Any, b: Any) -> float:
    arr_a = _to_numpy(a).astype(np.float64)
    arr_b = _to_numpy(b).astype(np.float64)
    return float(np.max(np.abs(arr_a - arr_b)))


def max_rel_error(a: Any, b: Any, denom_floor: float = 1e-30) -> float:
    arr_a = _to_numpy(a).astype(np.float64)
    arr_b = _to_numpy(b).astype(np.float64)
    denom = np.maximum(np.abs(arr_b), denom_floor)
    return float(np.max(np.abs(arr_a - arr_b) / denom))


def summarize_numeric_diff(a: Any, b: Any, rtol: float = 1e-6, atol: float = 1e-6) -> dict[str, Any]:
    return {
        "exact_match": compare_arrays_exact(a, b),
        "allclose": compare_arrays_close(a, b, rtol=rtol, atol=atol),
        "max_abs_error": max_abs_error(a, b),
        "max_rel_error": max_rel_error(a, b),
        "rtol": rtol,
        "atol": atol,
    }


def check_output_changes(output_a: Any, output_b: Any, min_abs_diff: float = 0.0) -> dict[str, Any]:
    abs_diff = max_abs_error(output_a, output_b)
    return {
        "max_abs_diff": abs_diff,
        "changed": abs_diff > min_abs_diff,
        "min_abs_diff_threshold": min_abs_diff,
    }


def check_input_sensitivity(model: Any, input_a: Any, input_b: Any, min_abs_diff: float = 0.0) -> dict[str, Any]:
    with_output = []
    for inp in (input_a, input_b):
        output = model(inp)
        if hasattr(output, "detach"):
            output = output.detach()
        if hasattr(output, "cpu"):
            output = output.cpu()
        if hasattr(output, "numpy"):
            output = output.numpy()
        with_output.append(output)

    result = check_output_changes(with_output[0], with_output[1], min_abs_diff=min_abs_diff)
    result["input_sensitivity_pass"] = result["changed"]
    return result


def assert_not_frozen(model: Any, input_a: Any, input_b: Any, min_abs_diff: float = 0.0) -> dict[str, Any]:
    result = check_input_sensitivity(model, input_a, input_b, min_abs_diff=min_abs_diff)
    if not result["input_sensitivity_pass"]:
        raise ValueError("Model output appears frozen across distinct inputs.")
    return result


def parse_floats_from_text(text: str) -> list[float]:
    return [float(token) for token in FLOAT_PATTERN.findall(text)]


def parse_float_matrix_from_text(text: str, rows: int, cols: int, take_last: bool = True) -> np.ndarray:
    values = parse_floats_from_text(text)
    expected = rows * cols
    if len(values) < expected:
        raise ValueError(f"Found {len(values)} floats, expected at least {expected}.")
    selected = values[-expected:] if take_last else values[:expected]
    return np.array(selected, dtype=np.float64).reshape(rows, cols)


def normalize_array_for_diff(array: Any, decimals: int = 2) -> list[str]:
    arr = _to_numpy(array).astype(np.float64)
    fmt = f"{{:.{decimals}f}}"
    return [fmt.format(value) for value in arr.ravel(order="C")]


def write_normalized_array(path: str | Path, array: Any, decimals: int = 2) -> Path:
    resolved = _as_path(path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    lines = normalize_array_for_diff(array, decimals=decimals)
    resolved.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return resolved


def run_text_diff(path_a: str | Path, path_b: str | Path, diff_out_path: str | Path | None = None) -> dict[str, Any]:
    resolved_a = assert_file_exists(path_a)
    resolved_b = assert_file_exists(path_b)
    proc = subprocess.run(
        ["diff", "-u", str(resolved_a), str(resolved_b)],
        capture_output=True,
        text=True,
        check=False,
    )
    diff_text = proc.stdout + proc.stderr
    if diff_out_path is not None:
        resolved_out = _as_path(diff_out_path).resolve()
        resolved_out.parent.mkdir(parents=True, exist_ok=True)
        resolved_out.write_text(diff_text, encoding="utf-8")
    else:
        resolved_out = None

    return {
        "path_a": str(resolved_a),
        "path_b": str(resolved_b),
        "diff_empty": proc.returncode == 0,
        "returncode": proc.returncode,
        "diff_output_path": str(resolved_out) if resolved_out else None,
        "diff_text": diff_text,
    }


def scan_warning_lines(paths: Sequence[str | Path]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for path in paths:
        resolved = _as_path(path).resolve()
        if not resolved.exists():
            continue
        text = resolved.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if re.search(r"warning|warn|deprecated", line, flags=re.IGNORECASE):
                warnings.append({
                    "file": str(resolved),
                    "line": line,
                })
    return warnings
