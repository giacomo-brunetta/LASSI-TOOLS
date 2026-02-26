import json
import os
import random
from datetime import datetime, timezone
from itertools import permutations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import tensorflow as tf


SEED = 1234
INPUT_SHAPE = (1, 240, 1)
EXPECTED_OUTPUT_ORDER = ["z_mean", "z_log_var"]


def set_determinism() -> None:
    os.environ["PYTHONHASHSEED"] = str(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def load_manifest(manifest_path: Path) -> Dict[str, str]:
    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def make_inputs() -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    x_primary = rng.normal(loc=0.0, scale=1.0, size=INPUT_SHAPE).astype(np.float32)
    x_secondary = rng.normal(loc=0.5, scale=1.2, size=INPUT_SHAPE).astype(np.float32)
    return x_primary, x_secondary


def save_inputs(path: Path, x_primary: np.ndarray, x_secondary: np.ndarray) -> None:
    np.savez(path, x_primary=x_primary, x_secondary=x_secondary)


def sanitize(name: str) -> str:
    return name.replace("/", "_")


def np_stats(arr: np.ndarray) -> Dict[str, float]:
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
    }


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=_json_default)


def _json_default(obj: object):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def run_savedmodel(
    model_dir: str,
    x: np.ndarray,
    source_key_order: List[str] | None = None,
) -> Tuple[Dict[str, np.ndarray], List[str]]:
    model = tf.saved_model.load(model_dir)
    infer = model.signatures["serving_default"]
    input_key = list(infer.structured_input_signature[1].keys())[0]
    out = infer(**{input_key: tf.convert_to_tensor(x, dtype=tf.float32)})
    out_np = {k: v.numpy() for k, v in out.items()}

    if source_key_order is None:
        if set(EXPECTED_OUTPUT_ORDER).issubset(out_np.keys()):
            source_key_order = EXPECTED_OUTPUT_ORDER.copy()
        else:
            source_key_order = list(out_np.keys())

    if len(source_key_order) < 2:
        raise RuntimeError(f"SavedModel outputs are insufficient for pinning: {source_key_order}")

    missing = [k for k in source_key_order if k not in out_np]
    if missing:
        if set(EXPECTED_OUTPUT_ORDER).issubset(out_np.keys()):
            source_key_order = EXPECTED_OUTPUT_ORDER.copy()
        else:
            source_key_order = list(out_np.keys())

    if len(source_key_order) < 2:
        raise RuntimeError(
            f"SavedModel outputs missing expected keys from baseline pinning map. Available={list(out_np.keys())}"
        )

    pinned = {
        EXPECTED_OUTPUT_ORDER[0]: out_np[source_key_order[0]],
        EXPECTED_OUTPUT_ORDER[1]: out_np[source_key_order[1]],
    }
    return pinned, source_key_order


def run_tflite(model_path: str, x: np.ndarray) -> Dict[str, object]:
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()

    if input_detail["dtype"] == np.int8:
        scale, zero_point = input_detail["quantization"]
        qx = np.round(x / scale + zero_point).astype(np.int8)
        interpreter.set_tensor(input_detail["index"], qx)
    else:
        interpreter.set_tensor(input_detail["index"], x.astype(input_detail["dtype"]))

    interpreter.invoke()

    raw_outputs: List[np.ndarray] = []
    dequant_outputs: List[np.ndarray] = []
    dtypes: List[str] = []
    for out in output_details:
        raw = interpreter.get_tensor(out["index"])
        raw_outputs.append(raw)
        dtypes.append(str(raw.dtype))
        if out["dtype"] == np.int8:
            scale, zero_point = out["quantization"]
            dequant_outputs.append((raw.astype(np.float32) - zero_point) * scale)
        else:
            dequant_outputs.append(raw.astype(np.float32))
    return {
        "raw_outputs": raw_outputs,
        "dequant_outputs": dequant_outputs,
        "raw_dtypes": dtypes,
    }


def pin_tflite_outputs_to_baseline(
    baseline: Dict[str, np.ndarray],
    tfl_dequant_outputs: List[np.ndarray],
) -> Tuple[Dict[str, np.ndarray], Dict[str, int], float]:
    if len(tfl_dequant_outputs) != 2:
        raise RuntimeError(f"Expected 2 TFLite outputs for pinning, got {len(tfl_dequant_outputs)}")

    best_perm = None
    best_score = float("inf")
    for perm in permutations(range(2)):
        score = 0.0
        for expected_idx, output_name in enumerate(EXPECTED_OUTPUT_ORDER):
            cand = tfl_dequant_outputs[perm[expected_idx]].astype(np.float32)
            ref = baseline[output_name].astype(np.float32)
            score += float(np.mean(np.abs(cand - ref)))
        if score < best_score:
            best_score = score
            best_perm = perm

    assert best_perm is not None
    pinned = {
        EXPECTED_OUTPUT_ORDER[0]: tfl_dequant_outputs[best_perm[0]],
        EXPECTED_OUTPUT_ORDER[1]: tfl_dequant_outputs[best_perm[1]],
    }
    mapping = {
        EXPECTED_OUTPUT_ORDER[0]: int(best_perm[0]),
        EXPECTED_OUTPUT_ORDER[1]: int(best_perm[1]),
    }
    return pinned, mapping, best_score


def compare_arrays(
    golden: np.ndarray,
    candidate: np.ndarray,
    rtol: float,
    atol: float,
) -> Dict[str, object]:
    golden = np.asarray(golden)
    candidate = np.asarray(candidate)
    is_integer_only = np.issubdtype(golden.dtype, np.integer) and np.issubdtype(candidate.dtype, np.integer)

    exact_equal = bool(np.array_equal(golden, candidate))
    max_abs = float(np.max(np.abs(golden.astype(np.float64) - candidate.astype(np.float64))))
    mean_abs = float(np.mean(np.abs(golden.astype(np.float64) - candidate.astype(np.float64))))

    if is_integer_only:
        within_tolerance = exact_equal
    else:
        within_tolerance = bool(np.allclose(golden, candidate, rtol=rtol, atol=atol, equal_nan=False))

    mismatch_idx = None
    if not exact_equal:
        diff = np.abs(golden.astype(np.float64) - candidate.astype(np.float64))
        flat_idx = int(np.argmax(diff))
        mismatch_idx = np.unravel_index(flat_idx, diff.shape)

    return {
        "shape": list(golden.shape),
        "golden_dtype": str(golden.dtype),
        "candidate_dtype": str(candidate.dtype),
        "integer_only": is_integer_only,
        "exact_equal": exact_equal,
        "within_tolerance": within_tolerance,
        "rtol": rtol,
        "atol": atol,
        "max_abs_error": max_abs,
        "mean_abs_error": mean_abs,
        "first_mismatch": {
            "index": list(mismatch_idx) if mismatch_idx is not None else None,
            "golden_value": float(golden[mismatch_idx]) if mismatch_idx is not None else None,
            "candidate_value": float(candidate[mismatch_idx]) if mismatch_idx is not None else None,
        },
    }


def classify_variant(comp: Dict[str, Dict[str, object]]) -> str:
    exact_all = all(v["exact_equal"] for v in comp.values())
    tol_all = all(v["within_tolerance"] for v in comp.values())
    if exact_all:
        return "IDENTICAL"
    if tol_all:
        return "ACCEPTABLE_NUMERIC_DRIFT"
    return "DIFF_EXISTS"


def tolerance_for_variant(name: str) -> Tuple[float, float]:
    if name in {"fp32_baseline_savedmodel", "graph_xla_savedmodel"}:
        return 1e-6, 1e-6
    if name in {"mixed_fp16_savedmodel", "mixed_bf16_savedmodel"}:
        return 5e-3, 5e-4
    if name == "ptq_float16_tflite":
        return 5e-3, 5e-4
    if name == "ptq_dynamic_int8":
        return 1e-2, 2e-3
    if name == "ptq_full_int8":
        return 2e-2, 5e-3
    return 1e-6, 1e-6


def run() -> None:
    set_determinism()
    root = Path(".")
    lassi_dir = root / "LASSI"
    artifacts_dir = lassi_dir / "verification_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(lassi_dir / "variant_manifest.json")

    x_primary, x_secondary = make_inputs()
    save_inputs(lassi_dir / "verification_inputs.npz", x_primary, x_secondary)

    baseline_model_path = str(root / "output" / "model" / "eels_encoder")
    golden_primary, baseline_source_key_order = run_savedmodel(baseline_model_path, x_primary)
    golden_secondary, _ = run_savedmodel(baseline_model_path, x_secondary, source_key_order=baseline_source_key_order)

    save_json(
        artifacts_dir / "baseline_golden_primary.json",
        {
            "output_order": EXPECTED_OUTPUT_ORDER,
            "baseline_source_output_keys": baseline_source_key_order,
            "z_mean": golden_primary["z_mean"].tolist(),
            "z_log_var": golden_primary["z_log_var"].tolist(),
            "z_mean_stats": np_stats(golden_primary["z_mean"]),
            "z_log_var_stats": np_stats(golden_primary["z_log_var"]),
        },
    )

    save_json(
        artifacts_dir / "baseline_golden_secondary.json",
        {
            "output_order": EXPECTED_OUTPUT_ORDER,
            "baseline_source_output_keys": baseline_source_key_order,
            "z_mean": golden_secondary["z_mean"].tolist(),
            "z_log_var": golden_secondary["z_log_var"].tolist(),
            "z_mean_stats": np_stats(golden_secondary["z_mean"]),
            "z_log_var_stats": np_stats(golden_secondary["z_log_var"]),
        },
    )

    variant_results: Dict[str, Dict[str, object]] = {}
    warning_summary: Dict[str, List[str]] = {}

    for variant_name, variant_path in manifest.items():
        rtol, atol = tolerance_for_variant(variant_name)
        variant_dir = artifacts_dir / sanitize(variant_name)
        variant_dir.mkdir(parents=True, exist_ok=True)

        warnings: List[str] = []
        output_mapping: Dict[str, object] = {
            "output_order": EXPECTED_OUTPUT_ORDER,
            "baseline_source_output_keys": baseline_source_key_order,
        }

        if not Path(variant_path).exists():
            warnings.append(f"Variant artifact missing at path: {variant_path}")
            variant_results[variant_name] = {
                "classification": "DIFF_EXISTS",
                "reason": "missing_variant_artifact",
                "tolerance": {"rtol": rtol, "atol": atol},
                "output_pinning": output_mapping,
                "warnings": warnings,
            }
            warning_summary[variant_name] = warnings
            save_json(variant_dir / "comparison_primary.json", variant_results[variant_name])
            continue

        if variant_name.endswith("_savedmodel"):
            cand_primary, _ = run_savedmodel(variant_path, x_primary, source_key_order=baseline_source_key_order)
            cand_secondary, _ = run_savedmodel(variant_path, x_secondary, source_key_order=baseline_source_key_order)
        elif variant_name in {"ptq_dynamic_int8", "ptq_full_int8", "ptq_float16_tflite"}:
            tfl_primary = run_tflite(variant_path, x_primary)
            tfl_secondary = run_tflite(variant_path, x_secondary)

            cand_primary, mapping, primary_score = pin_tflite_outputs_to_baseline(golden_primary, tfl_primary["dequant_outputs"])
            cand_secondary = {
                EXPECTED_OUTPUT_ORDER[0]: tfl_secondary["dequant_outputs"][mapping[EXPECTED_OUTPUT_ORDER[0]]],
                EXPECTED_OUTPUT_ORDER[1]: tfl_secondary["dequant_outputs"][mapping[EXPECTED_OUTPUT_ORDER[1]]],
            }
            output_mapping.update(
                {
                    "tflite_output_index_mapping": mapping,
                    "primary_mapping_score_mean_abs_sum": float(primary_score),
                    "raw_output_dtypes": tfl_primary["raw_dtypes"],
                }
            )
        else:
            warnings.append(f"Unknown variant '{variant_name}' in manifest; defaulting to DIFF_EXISTS classification.")
            variant_results[variant_name] = {
                "classification": "DIFF_EXISTS",
                "reason": "unknown_variant",
                "warnings": warnings,
            }
            continue

        save_json(
            variant_dir / "candidate_primary.json",
            {
                "output_order": EXPECTED_OUTPUT_ORDER,
                "z_mean": cand_primary["z_mean"].tolist(),
                "z_log_var": cand_primary["z_log_var"].tolist(),
                "z_mean_stats": np_stats(cand_primary["z_mean"]),
                "z_log_var_stats": np_stats(cand_primary["z_log_var"]),
            },
        )

        save_json(
            variant_dir / "candidate_secondary.json",
            {
                "output_order": EXPECTED_OUTPUT_ORDER,
                "z_mean": cand_secondary["z_mean"].tolist(),
                "z_log_var": cand_secondary["z_log_var"].tolist(),
                "z_mean_stats": np_stats(cand_secondary["z_mean"]),
                "z_log_var_stats": np_stats(cand_secondary["z_log_var"]),
            },
        )

        comparison = {
            out_name: compare_arrays(golden_primary[out_name], cand_primary[out_name], rtol=rtol, atol=atol)
            for out_name in EXPECTED_OUTPUT_ORDER
        }
        classification = classify_variant(comparison)

        sensitivity = {}
        for out_name in EXPECTED_OUTPUT_ORDER:
            g_diff = float(np.max(np.abs(golden_primary[out_name] - golden_secondary[out_name])))
            c_diff = float(np.max(np.abs(cand_primary[out_name] - cand_secondary[out_name])))
            sensitivity[out_name] = {
                "baseline_distinct_inputs_change_max_abs": g_diff,
                "candidate_distinct_inputs_change_max_abs": c_diff,
                "baseline_sensitive": bool(g_diff > 0.0),
                "candidate_sensitive": bool(c_diff > 0.0),
            }
            if not sensitivity[out_name]["candidate_sensitive"]:
                warnings.append(f"Input sensitivity failed for output {out_name}: no change across distinct inputs.")

        has_nan_inf = {
            out_name: {
                "contains_nan": bool(np.isnan(cand_primary[out_name]).any()),
                "contains_inf": bool(np.isinf(cand_primary[out_name]).any()),
            }
            for out_name in EXPECTED_OUTPUT_ORDER
        }
        for out_name, checks in has_nan_inf.items():
            if checks["contains_nan"] or checks["contains_inf"]:
                warnings.append(f"Numerical stability warning for {out_name}: NaN/Inf detected.")

        if warnings and classification != "DIFF_EXISTS":
            classification = "DIFF_EXISTS"

        variant_results[variant_name] = {
            "classification": classification,
            "tolerance": {"rtol": rtol, "atol": atol},
            "output_pinning": output_mapping,
            "comparison_primary": comparison,
            "input_sensitivity": sensitivity,
            "nan_inf_check": has_nan_inf,
            "warnings": warnings,
        }
        warning_summary[variant_name] = warnings

        save_json(variant_dir / "comparison_primary.json", variant_results[variant_name])

    overall_gate = "PASS" if all(v.get("classification") in {"IDENTICAL", "ACCEPTABLE_NUMERIC_DRIFT"} for v in variant_results.values()) else "FAIL"

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed_settings": {
            "pythonhashseed": str(SEED),
            "python_random_seed": SEED,
            "numpy_seed": SEED,
            "tensorflow_seed": SEED,
        },
        "baseline_model_path": baseline_model_path,
        "manifest": manifest,
        "output_order_pinned": EXPECTED_OUTPUT_ORDER,
        "variant_results": variant_results,
        "overall_verification_gate": overall_gate,
    }

    save_json(lassi_dir / "verification_results.json", summary)

    print(json.dumps({
        "overall_verification_gate": overall_gate,
        "variant_classification": {k: v["classification"] for k, v in variant_results.items()},
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
