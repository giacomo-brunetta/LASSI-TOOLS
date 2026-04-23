# aten.Bool.Tensor

- Status: ❌ Unsupported
- Error: Boolean value of Tensor with more than one value is ambiguous

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Boolean value of Tensor with more than one value is ambiguous
  spec=a: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=Boolean value of Tensor with more than one value is ambiguous
  spec=a: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
