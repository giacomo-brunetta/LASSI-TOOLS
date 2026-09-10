# aten.select_scatter

- Status: ❌ Unsupported
- Error: expected src to have a size equal to the slice of self. src size = [2, 3], slice size = [2]

## Attempts

- `float32_default`: unsupported; dtype=float32; error=expected src to have a size equal to the slice of self. src size = [2, 3], slice size = [2]
  spec=self: shape=(2, 3) dtype=float32; src: shape=(2, 3) dtype=float32; dim: 1; index: 1
- `int32_default`: unsupported; dtype=int32; error=expected src to have a size equal to the slice of self. src size = [2, 3], slice size = [2]
  spec=self: shape=(2, 3) dtype=int32; src: shape=(2, 3) dtype=int32; dim: 1; index: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
