# aten.Float.Tensor

- Status: ❌ Unsupported
- Error: a Tensor with 6 elements cannot be converted to Scalar

## Attempts

- `float32_default`: unsupported; dtype=float32; error=a Tensor with 6 elements cannot be converted to Scalar
  spec=a: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=a Tensor with 6 elements cannot be converted to Scalar
  spec=a: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
