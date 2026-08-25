# aten.fake_quantize_per_tensor_affine.tensor_qparams

- Status: ❌ Unsupported
- Error: a Tensor with 6 elements cannot be converted to Scalar

## Attempts

- `float32_default`: unsupported; dtype=float32; error=a Tensor with 6 elements cannot be converted to Scalar
  spec=self: shape=(2, 3) dtype=float32; scale: shape=(2, 3) dtype=float32; zero_point: shape=(2, 3) dtype=float32; quant_min: 1; quant_max: 1
- `int32_default`: unsupported; dtype=int32; error=a Tensor with 6 elements cannot be converted to Scalar
  spec=self: shape=(2, 3) dtype=int32; scale: shape=(2, 3) dtype=int32; zero_point: shape=(2, 3) dtype=int32; quant_min: 1; quant_max: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
