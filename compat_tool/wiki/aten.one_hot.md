# aten.one_hot

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=int64; num_classes: 4
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int64; num_classes: 4
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
