# aten.embedding_bag.padding_idx

- Status: ❌ Unsupported
- Error: embedding_bag: per_sample_weights only supported with mode='sum'

## Attempts

- `float32_default`: unsupported; dtype=float32; error=embedding_bag: per_sample_weights only supported with mode='sum'
  spec=weight: shape=(2, 3) dtype=float32; indices: shape=(2, 3) dtype=int64; offsets: shape=(2,) dtype=int64; scale_grad_by_freq: False; mode: 1; sparse: False; per_sample_weights: shape=(2, 3) dtype=float32; include_last_offset: False; padding_idx: -1
- `int32_default`: unsupported; dtype=int32; error=Expected tensor for argument #1 'weight' to have one of the following scalar types: Half, BFloat16, Float, Double; but got torch.IntTensor instead (while checking arguments for embedding_bag)
  spec=weight: shape=(2, 3) dtype=int32; indices: shape=(2, 3) dtype=int64; offsets: shape=(2,) dtype=int64; scale_grad_by_freq: False; mode: 1; sparse: False; per_sample_weights: shape=(2, 3) dtype=int32; include_last_offset: False; padding_idx: -1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
