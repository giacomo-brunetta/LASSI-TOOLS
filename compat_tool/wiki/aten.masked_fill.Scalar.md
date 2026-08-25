# aten.masked_fill.Scalar

- Status: ❌ Unsupported
- Error: masked_fill_ only supports boolean masks, but got mask with dtype float

## Attempts

- `float32_default`: unsupported; dtype=float32; error=masked_fill_ only supports boolean masks, but got mask with dtype float
  spec=self: shape=(2, 3) dtype=float32; mask: shape=(2, 3) dtype=float32; value: 1.0
- `int32_default`: unsupported; dtype=int32; error=masked_fill_ only supports boolean masks, but got mask with dtype int
  spec=self: shape=(2, 3) dtype=int32; mask: shape=(2, 3) dtype=int32; value: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
