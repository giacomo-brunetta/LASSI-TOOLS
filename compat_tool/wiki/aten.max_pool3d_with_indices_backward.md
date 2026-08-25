# aten.max_pool3d_with_indices_backward

- Status: ❌ Unsupported
- Error: expected scalar type Long but found Int

## Attempts

- `float32_default`: unsupported; dtype=float32; error=expected scalar type Long but found Int
  spec=grad_output: shape=(1, 2, 6, 6, 6) dtype=float32; self: shape=(1, 2, 6, 6, 6) dtype=float32; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; dilation: [1, 1, 1]; ceil_mode: False; indices: shape=(1, 2, 6, 6, 6) dtype=int32
- `int32_default`: unsupported; dtype=int32; error="max_pool3d_backward" not implemented for 'Int'
  spec=grad_output: shape=(1, 2, 6, 6, 6) dtype=int32; self: shape=(1, 2, 6, 6, 6) dtype=int32; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; dilation: [1, 1, 1]; ceil_mode: False; indices: shape=(1, 2, 6, 6, 6) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
