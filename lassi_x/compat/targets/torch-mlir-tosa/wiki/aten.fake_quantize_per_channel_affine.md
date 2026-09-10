# aten.fake_quantize_per_channel_affine

- Status: ❌ Unsupported
- Error: `zero_point` must be between `quant_min` and `quant_max`.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=`zero_point` must be between `quant_min` and `quant_max`.
  spec=self: shape=(2, 3) dtype=float32; scale: shape=(3,) dtype=float32; zero_point: shape=(3,) dtype=int32; axis: 1; quant_min: 1; quant_max: 1
- `int32_default`: unsupported; dtype=int32; error=`zero_point` must be between `quant_min` and `quant_max`.
  spec=self: shape=(2, 3) dtype=int32; scale: shape=(3,) dtype=float32; zero_point: shape=(3,) dtype=int32; axis: 1; quant_min: 1; quant_max: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
