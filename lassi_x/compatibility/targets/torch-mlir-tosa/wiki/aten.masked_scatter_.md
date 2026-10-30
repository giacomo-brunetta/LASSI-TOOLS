# aten.masked_scatter_

- Status: ❌ Unsupported
- Error: masked_scatter_ only supports boolean masks, but got mask with dtype Float

## Attempts

- `float32_default`: unsupported; dtype=float32; error=masked_scatter_ only supports boolean masks, but got mask with dtype Float
  spec=self: shape=(2, 3) dtype=float32; mask: shape=(2, 3) dtype=float32; source: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=masked_scatter_ only supports boolean masks, but got mask with dtype Int
  spec=self: shape=(2, 3) dtype=int32; mask: shape=(2, 3) dtype=int32; source: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
