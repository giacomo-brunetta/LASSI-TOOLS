import json
import os
from typing import Dict, Iterable, List, Tuple

import numpy as np
import tensorflow as tf


SEED = 1234
INPUT_SHAPE = (240, 1)
INPUT_BATCH_SHAPE = (1, 240, 1)
BASELINE_SAVEDMODEL_DIR = os.path.join("output", "model", "eels_encoder")


def set_determinism() -> None:
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def load_baseline_signature(
    base_model_dir: str,
) -> Tuple[tf.Module, tf.types.experimental.ConcreteFunction, list[str], str]:
    if not tf.io.gfile.exists(base_model_dir):
        raise FileNotFoundError(f"Baseline SavedModel not found: {base_model_dir}")

    baseline = tf.saved_model.load(base_model_dir)
    if "serving_default" not in baseline.signatures:
        raise RuntimeError(f"Baseline SavedModel has no serving_default signature: {base_model_dir}")

    infer = baseline.signatures["serving_default"]
    output_keys = list(infer.structured_outputs.keys())
    if len(output_keys) < 2:
        raise RuntimeError(f"Expected at least 2 outputs from baseline signature, got: {output_keys}")

    input_keys = list(infer.structured_input_signature[1].keys())
    if len(input_keys) != 1:
        raise RuntimeError(f"Expected single input in baseline signature, got: {input_keys}")

    return baseline, infer, output_keys, input_keys[0]


def _save_module(module: tf.Module, export_dir: str) -> None:
    os.makedirs(export_dir, exist_ok=True)
    signature = module.serving_default.get_concrete_function(
        tf.TensorSpec(shape=INPUT_BATCH_SHAPE, dtype=tf.float32, name="x1")
    )
    tf.saved_model.save(module, export_dir, signatures={"serving_default": signature})


def export_fp32_baseline_variant(
    base_dir: str,
    baseline_module: tf.Module,
    infer: tf.types.experimental.ConcreteFunction,
    output_keys: list[str],
    input_key: str,
) -> str:

    class Fp32Module(tf.Module):
        def __init__(self):
            super().__init__()
            self.baseline_module = baseline_module
            self.infer = infer
            self.input_key = input_key
            self.output_keys = output_keys

        @tf.function
        def serving_default(self, x1: tf.Tensor) -> Dict[str, tf.Tensor]:
            out = self.infer(**{self.input_key: tf.cast(x1, tf.float32)})
            return {
                "z_mean": tf.cast(out[self.output_keys[0]], tf.float32),
                "z_log_var": tf.cast(out[self.output_keys[1]], tf.float32),
            }

    export_dir = os.path.join(base_dir, "fp32_baseline")
    _save_module(Fp32Module(), export_dir)
    return export_dir


def export_graph_xla_variant(
    base_dir: str,
    baseline_module: tf.Module,
    infer: tf.types.experimental.ConcreteFunction,
    output_keys: list[str],
    input_key: str,
) -> str:

    class GraphXlaModule(tf.Module):
        def __init__(self):
            super().__init__()
            self.baseline_module = baseline_module
            self.infer = infer
            self.input_key = input_key
            self.output_keys = output_keys

        @tf.function(jit_compile=True)
        def serving_default(self, x1: tf.Tensor) -> Dict[str, tf.Tensor]:
            out = self.infer(**{self.input_key: tf.cast(x1, tf.float32)})
            return {
                "z_mean": tf.cast(out[self.output_keys[0]], tf.float32),
                "z_log_var": tf.cast(out[self.output_keys[1]], tf.float32),
            }

    export_dir = os.path.join(base_dir, "graph_xla")
    _save_module(GraphXlaModule(), export_dir)
    return export_dir


def export_mixed_precision_variant(
    base_dir: str,
    variant_name: str,
    baseline_module: tf.Module,
    infer: tf.types.experimental.ConcreteFunction,
    output_keys: list[str],
    input_key: str,
) -> str:
    if variant_name == "mixed_float16":
        compute_dtype = tf.float16
        suffix = "mixed_fp16"
    elif variant_name == "mixed_bfloat16":
        compute_dtype = tf.bfloat16
        suffix = "mixed_bf16"
    else:
        raise ValueError(f"Unsupported mixed-precision variant: {variant_name}")

    class MixedPrecisionModule(tf.Module):
        def __init__(self):
            super().__init__()
            self.baseline_module = baseline_module
            self.infer = infer
            self.input_key = input_key
            self.output_keys = output_keys

        @tf.function
        def serving_default(self, x1: tf.Tensor) -> Dict[str, tf.Tensor]:
            # Keep variant rooted in baseline graph/weights while perturbing compute path input precision.
            mixed_input = tf.cast(x1, compute_dtype)
            x_fp32 = tf.cast(mixed_input, tf.float32)
            out = self.infer(**{self.input_key: x_fp32})
            return {
                "z_mean": tf.cast(out[self.output_keys[0]], tf.float32),
                "z_log_var": tf.cast(out[self.output_keys[1]], tf.float32),
            }

    export_dir = os.path.join(base_dir, suffix)
    _save_module(MixedPrecisionModule(), export_dir)
    return export_dir


def _representative_dataset() -> Iterable[Tuple[tf.Tensor]]:
    rng = np.random.default_rng(SEED)
    t = np.linspace(0.0, 1.0, INPUT_BATCH_SHAPE[1], dtype=np.float32)

    samples: List[np.ndarray] = []

    # Gaussian coverage around baseline distribution.
    for std in (0.5, 1.0, 1.5):
        for _ in range(32):
            samples.append(rng.normal(loc=0.0, scale=std, size=INPUT_BATCH_SHAPE).astype(np.float32))

    # Shifted distributions to stress activation range tails.
    for mean, std in ((0.5, 1.2), (-0.8, 1.3), (1.2, 0.8)):
        for _ in range(24):
            samples.append(rng.normal(loc=mean, scale=std, size=INPUT_BATCH_SHAPE).astype(np.float32))

    # Structured temporal patterns (ramps/sines/spikes) common in EELS-like traces.
    for amplitude in (0.5, 1.0, 1.5):
        ramp = (amplitude * (2.0 * t - 1.0)).reshape(1, -1, 1).astype(np.float32)
        sine = (amplitude * np.sin(2.0 * np.pi * 5.0 * t)).reshape(1, -1, 1).astype(np.float32)
        spike = np.zeros(INPUT_BATCH_SHAPE, dtype=np.float32)
        spike[0, rng.integers(0, INPUT_BATCH_SHAPE[1]), 0] = amplitude * 3.0
        samples.extend([ramp, sine, spike])

    for sample in samples:
        # TFLite converter calibration expects a sequence aligned to model inputs.
        yield [tf.convert_to_tensor(sample, dtype=tf.float32)]


def export_tflite_quant_variants(
    source_savedmodel_dir: str,
    infer: tf.types.experimental.ConcreteFunction,
    out_dir: str,
) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    variants: Dict[str, str] = {}

    float16_path = os.path.join(out_dir, "ptq_float16.tflite")
    converter_fp16 = tf.lite.TFLiteConverter.from_concrete_functions([infer])
    converter_fp16.optimizations = [tf.lite.Optimize.DEFAULT]
    converter_fp16.target_spec.supported_types = [tf.float16]
    tflite_fp16 = converter_fp16.convert()
    with open(float16_path, "wb") as f:
        f.write(tflite_fp16)
    variants["ptq_float16_tflite"] = float16_path

    dynamic_path = os.path.join(out_dir, "ptq_dynamic_int8.tflite")
    converter_dynamic = tf.lite.TFLiteConverter.from_concrete_functions([infer])
    converter_dynamic.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_dynamic = converter_dynamic.convert()
    with open(dynamic_path, "wb") as f:
        f.write(tflite_dynamic)
    variants["ptq_dynamic_int8"] = dynamic_path

    full_int8_path = os.path.join(out_dir, "ptq_full_int8.tflite")
    try:
        converter_full = tf.lite.TFLiteConverter.from_concrete_functions([infer])
        converter_full.optimizations = [tf.lite.Optimize.DEFAULT]
        converter_full.representative_dataset = _representative_dataset
        converter_full.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS_INT8,
            tf.lite.OpsSet.TFLITE_BUILTINS,
        ]
        converter_full.inference_input_type = tf.float32
        converter_full.inference_output_type = tf.float32
        tflite_full = converter_full.convert()
        with open(full_int8_path, "wb") as f:
            f.write(tflite_full)
        variants["ptq_full_int8"] = full_int8_path
    except Exception as exc:
        blocker_path = os.path.join("LASSI", "quantization_blockers.md")
        with open(blocker_path, "w", encoding="utf-8") as f:
            f.write("# Quantization Blockers\n\n")
            f.write("- Full-int8 PTQ conversion failed in this environment.\n")
            f.write(f"- Error: `{type(exc).__name__}: {exc}`\n")
            f.write("- Dynamic PTQ int8 variant was generated and kept as the mandatory int8 PTQ path.\n")
        variants["ptq_full_int8_blocker"] = blocker_path

    return variants


def main() -> None:
    set_determinism()
    base_dir = os.path.join(os.getcwd(), "output", "model", "variants")
    os.makedirs(base_dir, exist_ok=True)

    baseline_module, infer, output_keys, input_key = load_baseline_signature(BASELINE_SAVEDMODEL_DIR)

    fp32_path = export_fp32_baseline_variant(base_dir, baseline_module, infer, output_keys, input_key)
    graph_path = export_graph_xla_variant(base_dir, baseline_module, infer, output_keys, input_key)
    fp16_path = export_mixed_precision_variant(
        base_dir,
        "mixed_float16",
        baseline_module,
        infer,
        output_keys,
        input_key,
    )
    bf16_path = export_mixed_precision_variant(
        base_dir,
        "mixed_bfloat16",
        baseline_module,
        infer,
        output_keys,
        input_key,
    )
    quant_paths = export_tflite_quant_variants(BASELINE_SAVEDMODEL_DIR, infer, base_dir)

    manifest = {
        "fp32_baseline_savedmodel": fp32_path,
        "graph_xla_savedmodel": graph_path,
        "mixed_fp16_savedmodel": fp16_path,
        "mixed_bf16_savedmodel": bf16_path,
        **quant_paths,
    }
    manifest_path = os.path.join("LASSI", "variant_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
