# aten.fill.Tensor

- Status: ❌ Unsupported
- Error: fill_ only supports 0-dimension value tensor but got tensor with 2 dimensions.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=fill_ only supports 0-dimension value tensor but got tensor with 2 dimensions.
  spec=self: shape=(2, 3) dtype=float32; value: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=fill_ only supports 0-dimension value tensor but got tensor with 2 dimensions.
  spec=self: shape=(2, 3) dtype=int32; value: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
