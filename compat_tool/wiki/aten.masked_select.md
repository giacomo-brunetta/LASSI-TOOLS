# aten.masked_select

- Status: ❌ Unsupported
- Error: masked_select: expected BoolTensor for mask

## Attempts

- `float32_default`: unsupported; dtype=float32; error=masked_select: expected BoolTensor for mask
  spec=self: shape=(2, 3) dtype=float32; mask: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=masked_select: expected BoolTensor for mask
  spec=self: shape=(2, 3) dtype=int32; mask: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
