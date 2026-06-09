# aten.scatter_.src

- Status: ❌ Unsupported
- Error: scatter(): Expected dtype int64 for index

## Attempts

- `float32_default`: unsupported; dtype=float32; error=scatter(): Expected dtype int64 for index
  spec=self: shape=(2, 3) dtype=float32; dim: 1; index: shape=(2, 3) dtype=int32; src: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=scatter(): Expected dtype int64 for index
  spec=self: shape=(2, 3) dtype=int32; dim: 1; index: shape=(2, 3) dtype=int32; src: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
