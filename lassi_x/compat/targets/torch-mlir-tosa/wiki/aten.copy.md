# aten.copy

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; src: shape=(2, 3) dtype=float32; non_blocking: False
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; src: shape=(2, 3) dtype=int32; non_blocking: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
