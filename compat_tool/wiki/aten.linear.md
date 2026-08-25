# aten.linear

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=input: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; bias: None
- `int32_default`: supported; dtype=int32; error=None
  spec=input: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; bias: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
