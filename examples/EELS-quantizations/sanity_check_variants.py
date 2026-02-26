import json
import os
from typing import Dict, List, Tuple

import numpy as np
import tensorflow as tf


SEED = 1234
INPUT_SHAPE = (1, 240, 1)


def _load_manifest() -> Dict[str, str]:
    with open(os.path.join("LASSI", "variant_manifest.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def _make_inputs() -> Tuple[np.ndarray, np.ndarray]:
    np.random.seed(SEED)
    x_a = np.random.normal(0.0, 1.0, size=INPUT_SHAPE).astype(np.float32)
    x_b = np.random.normal(0.5, 1.2, size=INPUT_SHAPE).astype(np.float32)
    return x_a, x_b


def _savedmodel_run(model_dir: str, x: np.ndarray) -> Dict[str, np.ndarray]:
    model = tf.saved_model.load(model_dir)
    infer = model.signatures["serving_default"]
    input_key = list(infer.structured_input_signature[1].keys())[0]
    y = infer(**{input_key: tf.convert_to_tensor(x, dtype=tf.float32)})
    return {k: v.numpy() for k, v in y.items()}


def _tflite_run(model_path: str, x: np.ndarray) -> List[np.ndarray]:
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
    outputs: List[np.ndarray] = []
    for out in output_details:
        raw = interpreter.get_tensor(out["index"])
        if out["dtype"] == np.int8:
            scale, zero_point = out["quantization"]
            outputs.append((raw.astype(np.float32) - zero_point) * scale)
        else:
            outputs.append(raw.astype(np.float32))
    return outputs


def main() -> None:
    manifest = _load_manifest()
    x_a, x_b = _make_inputs()

    result: Dict[str, Dict[str, object]] = {}

    for key, variant_path in manifest.items():
        if not key.endswith("_savedmodel"):
            continue
        out_a = _savedmodel_run(variant_path, x_a)
        out_b = _savedmodel_run(variant_path, x_b)
        result[key] = {
            "io_contract": {
                "input_shape": list(x_a.shape),
                "input_dtype": "float32",
                "outputs": {
                    name: {"shape": list(val.shape), "dtype": str(val.dtype)}
                    for name, val in out_a.items()
                },
            },
            "input_sensitivity": {
                name: bool(not np.allclose(out_a[name], out_b[name]))
                for name in out_a.keys()
            },
        }

    for key, variant_path in manifest.items():
        if not str(variant_path).endswith(".tflite"):
            continue
        out_a = _tflite_run(variant_path, x_a)
        out_b = _tflite_run(variant_path, x_b)
        result[key] = {
            "io_contract": {
                "input_shape": list(x_a.shape),
                "input_dtype": "float32",
                "num_outputs": len(out_a),
                "outputs": [
                    {"shape": list(arr.shape), "dtype": str(arr.dtype)} for arr in out_a
                ],
            },
            "input_sensitivity": [bool(not np.allclose(a, b)) for a, b in zip(out_a, out_b)],
        }

    out_path = os.path.join("LASSI", "variant_sanity.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
