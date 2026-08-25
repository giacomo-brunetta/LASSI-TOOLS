# aten.mv

- Status: ❌ Unsupported
- Error: vector + matrix @ vector expected, got 1, 2, 2

## Attempts

- `float32_default`: unsupported; dtype=float32; error=vector + matrix @ vector expected, got 1, 2, 2
  spec=self: shape=(2, 3) dtype=float32; vec: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=vector + matrix @ vector expected, got 1, 2, 2
  spec=self: shape=(2, 3) dtype=int32; vec: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
