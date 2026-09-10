# aten.narrow.Tensor

- Status: ❌ Unsupported
- Error: start must be an 0-dim integral Tensor.
- Alternative: Use `aten.narrow` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=start must be an 0-dim integral Tensor.
  spec=self: shape=(2, 3) dtype=float32; dim: 1; start: shape=(2, 3) dtype=float32; length: 1
- `int32_default`: unsupported; dtype=int32; error=start must be an 0-dim integral Tensor.
  spec=self: shape=(2, 3) dtype=int32; dim: 1; start: shape=(2, 3) dtype=int32; length: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
