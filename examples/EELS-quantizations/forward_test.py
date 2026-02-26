import tensorflow as tf

import tfscript


def main() -> None:
    # Build and export the encoder SavedModel if it does not exist yet.
    tfscript.build_and_save_encoder()

    model = tf.saved_model.load("output/model/eels_encoder")
    infer = model.signatures["serving_default"]
    input_keys = list(infer.structured_input_signature[1].keys())
    if len(input_keys) != 1:
        raise RuntimeError(f"Expected one input key, got: {input_keys}")
    input_key = input_keys[0]

    x = tf.random.normal([1, 240, 1], dtype=tf.float32)
    outputs = infer(**{input_key: x})

    print("Forward pass complete.")
    print(f"Input key used: {input_key}")
    for name, tensor in outputs.items():
        print(f"{name}: shape={tuple(tensor.shape)}, dtype={tensor.dtype.name}")
        print(f"{name} sample[0, :4] = {tensor.numpy()[0, :4]}")


if __name__ == "__main__":
    main()
