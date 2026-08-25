# aten.index_put_

- Status: ❌ Unsupported
- Error: shape mismatch: value tensor of shape [2, 3] cannot be broadcast to indexing result of shape [3]

## Attempts

- `float32_default`: unsupported; dtype=float32; error=shape mismatch: value tensor of shape [2, 3] cannot be broadcast to indexing result of shape [3]
  spec=self: shape=(2, 3) dtype=float32; indices: shape=(2, 3) dtype=int32; values: shape=(2, 3) dtype=float32; accumulate: False
- `int32_default`: unsupported; dtype=int32; error=shape mismatch: value tensor of shape [2, 3] cannot be broadcast to indexing result of shape [3]
  spec=self: shape=(2, 3) dtype=int32; indices: shape=(2, 3) dtype=int32; values: shape=(2, 3) dtype=int32; accumulate: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
