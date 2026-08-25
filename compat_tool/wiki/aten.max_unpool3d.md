# aten.max_unpool3d

- Status: ❌ Unsupported
- Error: elements in indices should be type int64

## Attempts

- `float32_default`: unsupported; dtype=float32; error=elements in indices should be type int64
  spec=self: shape=(1, 2, 6, 6, 6) dtype=float32; indices: shape=(1, 2, 6, 6, 6) dtype=int32; output_size: [4, 4, 4]; stride: [1, 1, 1]; padding: [0]
- `int32_default`: unsupported; dtype=int32; error=elements in indices should be type int64
  spec=self: shape=(1, 2, 6, 6, 6) dtype=int32; indices: shape=(1, 2, 6, 6, 6) dtype=int32; output_size: [4, 4, 4]; stride: [1, 1, 1]; padding: [0]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
