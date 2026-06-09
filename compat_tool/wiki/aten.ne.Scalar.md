# aten.ne.Scalar

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; other: 1.0
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; other: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
