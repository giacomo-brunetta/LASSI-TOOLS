# aten.outer

- Status: ❌ Unsupported
- Error: outer: Expected 1-D argument self, but got 2-D

## Attempts

- `float32_default`: unsupported; dtype=float32; error=outer: Expected 1-D argument self, but got 2-D
  spec=self: shape=(2, 3) dtype=float32; vec2: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=outer: Expected 1-D argument self, but got 2-D
  spec=self: shape=(2, 3) dtype=int32; vec2: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
