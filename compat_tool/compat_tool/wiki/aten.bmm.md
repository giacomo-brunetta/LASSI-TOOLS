# aten.bmm

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3, 4) dtype=float32; mat2: shape=(2, 4, 5) dtype=float32
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3, 4) dtype=int32; mat2: shape=(2, 4, 5) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
