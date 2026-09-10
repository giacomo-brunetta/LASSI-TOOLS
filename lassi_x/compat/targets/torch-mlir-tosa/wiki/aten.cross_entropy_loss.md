# aten.cross_entropy_loss

- Status: ❌ Unsupported
- Error: weight tensor should be defined either for all 3 classes or no classes but got weight tensor of shape: [2, 3]

## Attempts

- `float32_default`: unsupported; dtype=float32; error=weight tensor should be defined either for all 3 classes or no classes but got weight tensor of shape: [2, 3]
  spec=self: shape=(2, 3) dtype=float32; target: shape=(2,) dtype=int64; weight: shape=(2, 3) dtype=float32; reduction: 1; ignore_index: -100; label_smoothing: 1.0
- `int32_default`: unsupported; dtype=int32; error="log_softmax_lastdim_kernel_impl" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; target: shape=(2,) dtype=int64; weight: shape=(2, 3) dtype=int32; reduction: 1; ignore_index: -100; label_smoothing: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
