import json
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Tuple

import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2


MANIFEST_PATH = os.path.join("LASSI", "variant_manifest.json")
OUT_ROOT = os.path.join("output", "tosa_variants")
REPORT_PATH = os.path.join("LASSI", "tosa_generation_report.md")


def _resolve_tool(name: str) -> str:
    candidates = [name, os.path.join("/opt", "tensorflow", "bin", name)]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
        if os.path.sep not in c:
            found = subprocess.run(["/bin/bash", "-lc", f"command -v {name}"], capture_output=True, text=True)
            if found.returncode == 0:
                return found.stdout.strip()
    raise FileNotFoundError(f"Required tool not found: {name}")


@dataclass
class VariantResult:
    variant: str
    source: str
    status: str
    tosa_path: str
    details: str


def _run(cmd: List[str], log_path: str) -> None:
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log.write(proc.stdout)
        log.write("\n")
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed (exit={proc.returncode}): {' '.join(cmd)}")


def _frozen_from_savedmodel(savedmodel_dir: str, frozen_pbtxt: str) -> Tuple[str, str, str, str]:
    model = tf.saved_model.load(savedmodel_dir)
    if "serving_default" not in model.signatures:
        raise RuntimeError(f"Missing serving_default signature in {savedmodel_dir}")

    concrete = model.signatures["serving_default"]
    frozen = convert_variables_to_constants_v2(concrete)

    input_tensors = [t for t in frozen.inputs if t.dtype != tf.resource]
    if len(input_tensors) != 1:
        raise RuntimeError(
            f"Expected one non-resource input for {savedmodel_dir}, got {len(input_tensors)}"
        )

    in_tensor = input_tensors[0]
    in_name = in_tensor.name.split(":")[0]
    in_dtype = "DT_FLOAT" if in_tensor.dtype == tf.float32 else str(in_tensor.dtype.name)
    shape = ",".join(str(d if d is not None else 1) for d in in_tensor.shape.as_list())

    # Keep only first two outputs to match model contract used by forward/verification paths.
    out_nodes = ",".join(t.name.split(":")[0] for t in frozen.outputs[:2])

    out_dir = os.path.dirname(frozen_pbtxt)
    os.makedirs(out_dir, exist_ok=True)
    tf.io.write_graph(frozen.graph, out_dir, os.path.basename(frozen_pbtxt), as_text=True)
    return in_name, in_dtype, shape, out_nodes


def _validate_tosa(mlir_path: str) -> Tuple[bool, str]:
    if not os.path.exists(mlir_path):
        return False, "Missing TOSA file"
    text = open(mlir_path, "r", encoding="utf-8").read()
    if "func.func" not in text:
        return False, "Missing func.func"
    if "tosa." not in text:
        return False, "Missing tosa dialect ops"
    if "%arg" not in text:
        return False, "No runtime arg usage (%arg*)"

    nonconst = [line for line in text.splitlines() if "tosa." in line and "tosa.const" not in line]
    if not nonconst:
        return False, "Appears constants-only (no non-const tosa op)"

    return True, "Structure checks passed"


def _convert_savedmodel_variant(variant: str, source: str, out_dir: str) -> VariantResult:
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "conversion.log")
    frozen_pbtxt = os.path.join(out_dir, "frozen_graph.pbtxt")
    tf_mlir = os.path.join(out_dir, "tf.mlir")
    tosa_mlir = os.path.join(out_dir, "01_tosa.mlir")

    in_name, in_dtype, in_shape, out_nodes = _frozen_from_savedmodel(source, frozen_pbtxt)

    tf_mlir_translate = _resolve_tool("tf-mlir-translate")
    tf_opt = _resolve_tool("tf-opt")

    _run(
        [
            tf_mlir_translate,
            "--graphdef-to-mlir",
            f"--tf-input-arrays={in_name}",
            f"--tf-input-data-types={in_dtype}",
            f"--tf-input-shapes={in_shape}",
            f"--tf-output-arrays={out_nodes}",
            frozen_pbtxt,
            "-o",
            tf_mlir,
        ],
        log_path,
    )

    _run(
        [
            tf_opt,
            "--tf-executor-to-functional-conversion",
            "--tf-region-control-flow-to-functional",
            "--tf-shape-inference",
            "--tf-to-tosa-pipeline",
            tf_mlir,
            "-o",
            tosa_mlir,
        ],
        log_path,
    )

    ok, details = _validate_tosa(tosa_mlir)
    return VariantResult(variant, source, "PASS" if ok else "FAIL", tosa_mlir, details)


def _convert_tflite_variant(variant: str, source: str, out_dir: str) -> VariantResult:
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "conversion.log")
    tosa_mlir = os.path.join(out_dir, "01_tosa.mlir")

    flatbuffer_translate = _resolve_tool("flatbuffer_translate")
    tf_opt = _resolve_tool("tf-opt")
    tfl_mlir = os.path.join(out_dir, "00_tfl.mlir")

    _run(
        [
            flatbuffer_translate,
            "-tflite-flatbuffer-to-mlir",
            "-mlir-print-local-scope",
            "-emit-builtin-tflite-ops",
            "-lower-tensor-list-ops",
            source,
            "-o",
            tfl_mlir,
        ],
        log_path,
    )

    _run(
        [
            tf_opt,
            "-tf-executor-to-functional-conversion",
            "-tf-region-control-flow-to-functional",
            "-tf-shape-inference",
            "-tf-to-tosa-pipeline",
            "-tfl-to-tosa-pipeline",
            "-tf-tfl-to-tosa-pipeline",
            "-tosa-legalize-tfl",
            "-tosa-strip-quant-types",
            "-tosa-tflite-verify-fully-converted",
            tfl_mlir,
            "-o",
            tosa_mlir,
        ],
        log_path,
    )

    ok, details = _validate_tosa(tosa_mlir)
    return VariantResult(variant, source, "PASS" if ok else "FAIL", tosa_mlir, details)


def _write_report(results: List[VariantResult]) -> None:
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# TOSA Generation Report (All Variants)\n\n")
        f.write("| Variant | Source | Status | TOSA Path | Details |\n")
        f.write("|---|---|---|---|---|\n")
        for r in results:
            f.write(
                f"| `{r.variant}` | `{r.source}` | **{r.status}** | `{r.tosa_path}` | {r.details} |\n"
            )


def main() -> None:
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest: Dict[str, str] = json.load(f)

    results: List[VariantResult] = []
    for variant, source in manifest.items():
        out_dir = os.path.join(OUT_ROOT, variant)
        try:
            if source.endswith(".tflite"):
                result = _convert_tflite_variant(variant, source, out_dir)
            else:
                result = _convert_savedmodel_variant(variant, source, out_dir)
        except Exception as exc:  # pylint: disable=broad-except
            result = VariantResult(variant, source, "FAIL", os.path.join(out_dir, "01_tosa.mlir"), str(exc))
        results.append(result)

    _write_report(results)
    print(json.dumps([r.__dict__ for r in results], indent=2))


if __name__ == "__main__":
    main()
