# aten.embedding

- Status: ❌ Unsupported
- Error: index out of range in self

## Attempts

- `float32_default`: unsupported; dtype=float32; error=index out of range in self
  spec=weight: shape=(2, 3) dtype=float32; indices: shape=(2, 3) dtype=int64; padding_idx: -1; scale_grad_by_freq: False; sparse: False
- `int32_default`: unsupported; dtype=int32; error=index out of range in self
  spec=weight: shape=(2, 3) dtype=int32; indices: shape=(2, 3) dtype=int64; padding_idx: -1; scale_grad_by_freq: False; sparse: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
