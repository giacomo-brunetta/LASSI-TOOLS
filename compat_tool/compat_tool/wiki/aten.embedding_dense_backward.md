# aten.embedding_dense_backward

- Status: ❌ Unsupported
- Error: shape '[6, 3]' is invalid for input of size 6

## Attempts

- `float32_default`: unsupported; dtype=float32; error=shape '[6, 3]' is invalid for input of size 6
  spec=grad_output: shape=(2, 3) dtype=float32; indices: shape=(2, 3) dtype=int64; num_weights: 4; padding_idx: -1; scale_grad_by_freq: False
- `int32_default`: unsupported; dtype=int32; error=shape '[6, 3]' is invalid for input of size 6
  spec=grad_output: shape=(2, 3) dtype=int32; indices: shape=(2, 3) dtype=int64; num_weights: 4; padding_idx: -1; scale_grad_by_freq: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
