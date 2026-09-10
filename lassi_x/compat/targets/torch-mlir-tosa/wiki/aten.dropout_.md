# aten.dropout_

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; p: 1.0; train: False
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; p: 1; train: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
