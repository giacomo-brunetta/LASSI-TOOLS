# aten.nll_loss2d_backward

- Status: ❌ Unsupported
- Error: only batches of spatial targets supported (3D tensors) but got targets of dimension: 2

## Attempts

- `float32_default`: unsupported; dtype=float32; error=only batches of spatial targets supported (3D tensors) but got targets of dimension: 2
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; target: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; reduction: 1; ignore_index: -100; total_weight: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=only batches of spatial targets supported (3D tensors) but got targets of dimension: 2
  spec=grad_output: shape=(2, 3) dtype=int32; self: shape=(2, 3) dtype=int32; target: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; reduction: 1; ignore_index: -100; total_weight: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
