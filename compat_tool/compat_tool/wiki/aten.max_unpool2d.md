# aten.max_unpool2d

- Status: ❌ Unsupported
- Error: elements in indices should be type int64 but got: Int

## Attempts

- `float32_default`: unsupported; dtype=float32; error=elements in indices should be type int64 but got: Int
  spec=self: shape=(1, 2, 8, 8) dtype=float32; indices: shape=(1, 2, 8, 8) dtype=int32; output_size: [4, 4]
- `int32_default`: unsupported; dtype=int32; error=elements in indices should be type int64 but got: Int
  spec=self: shape=(1, 2, 8, 8) dtype=int32; indices: shape=(1, 2, 8, 8) dtype=int32; output_size: [4, 4]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
