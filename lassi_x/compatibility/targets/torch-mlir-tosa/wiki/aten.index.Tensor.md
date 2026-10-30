# aten.index.Tensor

- Status: ❌ Unsupported
- Error: index 3 is out of bounds for dimension 1 with size 3

## Attempts

- `float32_default`: unsupported; dtype=float32; error=index 3 is out of bounds for dimension 1 with size 3
  spec=self: shape=(2, 3) dtype=float32; indices: shape=(2, 3) dtype=int32
- `int32_default`: unsupported; dtype=int32; error=index 3 is out of bounds for dimension 1 with size 3
  spec=self: shape=(2, 3) dtype=int32; indices: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
