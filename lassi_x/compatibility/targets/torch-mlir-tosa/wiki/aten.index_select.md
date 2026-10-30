# aten.index_select

- Status: ❌ Unsupported
- Error: index_select(): Index is supposed to be a vector

## Attempts

- `float32_default`: unsupported; dtype=float32; error=index_select(): Index is supposed to be a vector
  spec=self: shape=(2, 3) dtype=float32; dim: 1; index: shape=(2, 3) dtype=int32
- `int32_default`: unsupported; dtype=int32; error=index_select(): Index is supposed to be a vector
  spec=self: shape=(2, 3) dtype=int32; dim: 1; index: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
