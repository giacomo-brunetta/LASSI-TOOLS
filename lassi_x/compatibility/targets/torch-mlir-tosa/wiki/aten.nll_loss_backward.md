# aten.nll_loss_backward

- Status: ❌ Unsupported
- Error: 0D or 1D target tensor expected, multi-target not supported

## Attempts

- `float32_default`: unsupported; dtype=float32; error=0D or 1D target tensor expected, multi-target not supported
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; target: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; reduction: 1; ignore_index: -100; total_weight: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=0D or 1D target tensor expected, multi-target not supported
  spec=grad_output: shape=(2, 3) dtype=int32; self: shape=(2, 3) dtype=int32; target: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; reduction: 1; ignore_index: -100; total_weight: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
