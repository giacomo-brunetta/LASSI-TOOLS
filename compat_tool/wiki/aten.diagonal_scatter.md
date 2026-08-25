# aten.diagonal_scatter

- Status: ❌ Unsupported
- Error: expected src to have a size equal to the slice of self. src size = [2, 3], slice size = [2]

## Attempts

- `float32_default`: unsupported; dtype=float32; error=expected src to have a size equal to the slice of self. src size = [2, 3], slice size = [2]
  spec=self: shape=(2, 3) dtype=float32; src: shape=(2, 3) dtype=float32; offset: 1; dim1: 0; dim2: 1
- `int32_default`: unsupported; dtype=int32; error=expected src to have a size equal to the slice of self. src size = [2, 3], slice size = [2]
  spec=self: shape=(2, 3) dtype=int32; src: shape=(2, 3) dtype=int32; offset: 1; dim1: 0; dim2: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
