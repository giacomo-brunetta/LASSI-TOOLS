from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import numpy as np


def _load_csv_array(path: str | Path) -> np.ndarray:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"CSV file not found: {resolved}")
    if resolved.stat().st_size == 0:
        raise ValueError(f"CSV file is empty: {resolved}")
    return np.loadtxt(resolved, delimiter=",", dtype=np.float64)


def _normalize_shape(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 0:
        return arr.reshape(1, 1)
    if arr.ndim == 1:
        return arr.reshape(-1, 1)
    return arr


async def summarize_csv_impl(path: str) -> str:
    array = _normalize_shape(_load_csv_array(path))
    summary = {
        "path": str(Path(path).resolve()),
        "shape": list(array.shape),
        "size": int(array.size),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
        "has_nan": bool(np.isnan(array).any()),
        "has_inf": bool(np.isinf(array).any()),
    }
    return json.dumps(summary, indent=2)


async def compare_csv_outputs_impl(
    golden_csv: str,
    candidate_csv: str,
    rtol: float = 1e-6,
    atol: float = 1e-6,
    expected_shape: list[int] | None = None,
) -> str:
    golden = _normalize_shape(_load_csv_array(golden_csv))
    candidate = _normalize_shape(_load_csv_array(candidate_csv))

    result: dict[str, Any] = {
        "golden_csv": str(Path(golden_csv).resolve()),
        "candidate_csv": str(Path(candidate_csv).resolve()),
        "golden_shape": list(golden.shape),
        "candidate_shape": list(candidate.shape),
        "rtol": rtol,
        "atol": atol,
    }

    if expected_shape is not None:
        result["expected_shape"] = expected_shape
        result["expected_shape_match"] = list(golden.shape) == expected_shape and list(candidate.shape) == expected_shape

    if golden.shape != candidate.shape:
        result["shape_match"] = False
        result["exact_match"] = False
        result["allclose"] = False
        result["error"] = "Shape mismatch"
        return json.dumps(result, indent=2)

    diff = candidate - golden
    abs_diff = np.abs(diff)
    rel_diff = abs_diff / np.maximum(np.abs(golden), 1e-30)
    exact_match = bool(np.array_equal(candidate, golden))
    allclose = bool(np.allclose(candidate, golden, rtol=rtol, atol=atol))

    flat_index = int(np.argmax(abs_diff))
    mismatch_index = [int(i) for i in np.unravel_index(flat_index, golden.shape)]

    result.update({
        "shape_match": True,
        "exact_match": exact_match,
        "allclose": allclose,
        "max_abs_error": float(np.max(abs_diff)),
        "max_rel_error": float(np.max(rel_diff)),
        "first_max_abs_mismatch_index": mismatch_index,
        "golden_value_at_first_max_abs_mismatch": float(golden[tuple(mismatch_index)]),
        "candidate_value_at_first_max_abs_mismatch": float(candidate[tuple(mismatch_index)]),
        "nan_in_golden": bool(np.isnan(golden).any()),
        "nan_in_candidate": bool(np.isnan(candidate).any()),
        "inf_in_golden": bool(np.isinf(golden).any()),
        "inf_in_candidate": bool(np.isinf(candidate).any()),
        "classification": (
            "IDENTICAL" if exact_match else
            "ACCEPTABLE_NUMERIC_DRIFT" if allclose else
            "DIFF_EXISTS"
        ),
    })

    return json.dumps(result, indent=2)


async def diff_csv_outputs_impl(
    golden_csv: str,
    candidate_csv: str,
    output_path: str | None = None,
    max_rows: int = 20,
) -> str:
    golden = _normalize_shape(_load_csv_array(golden_csv))
    candidate = _normalize_shape(_load_csv_array(candidate_csv))

    result: dict[str, Any] = {
        "golden_csv": str(Path(golden_csv).resolve()),
        "candidate_csv": str(Path(candidate_csv).resolve()),
        "golden_shape": list(golden.shape),
        "candidate_shape": list(candidate.shape),
    }

    if golden.shape != candidate.shape:
        result["shape_match"] = False
        result["error"] = "Shape mismatch"
        return json.dumps(result, indent=2)

    mismatches: list[dict[str, Any]] = []
    for index in np.argwhere(golden != candidate):
        idx = tuple(int(i) for i in index)
        mismatches.append({
            "index": list(idx),
            "golden": float(golden[idx]),
            "candidate": float(candidate[idx]),
            "abs_diff": float(abs(candidate[idx] - golden[idx])),
        })
        if len(mismatches) >= max_rows:
            break

    report = {
        **result,
        "shape_match": True,
        "mismatch_count": int(np.count_nonzero(golden != candidate)),
        "reported_mismatches": mismatches,
        "max_rows": max_rows,
    }

    if output_path:
        resolved_output = Path(output_path).resolve()
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report["output_path"] = str(resolved_output)

    return json.dumps(report, indent=2)
