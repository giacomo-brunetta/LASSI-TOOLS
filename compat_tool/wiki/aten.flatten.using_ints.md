# aten.flatten.using_ints

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; start_dim: 1; end_dim: 1
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; start_dim: 1; end_dim: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
