# aten.masked_fill.Tensor

- Status: ❌ Unsupported
- Error: masked_fill_ only supports a 0-dimensional value tensor, but got tensor with 2 dimension(s).

## Attempts

- `float32_default`: unsupported; dtype=float32; error=masked_fill_ only supports a 0-dimensional value tensor, but got tensor with 2 dimension(s).
  spec=self: shape=(2, 3) dtype=float32; mask: shape=(2, 3) dtype=float32; value: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=masked_fill_ only supports a 0-dimensional value tensor, but got tensor with 2 dimension(s).
  spec=self: shape=(2, 3) dtype=int32; mask: shape=(2, 3) dtype=int32; value: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
