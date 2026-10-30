# aten.to.other

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32; non_blocking: False; copy: False; memory_format: None
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32; non_blocking: False; copy: False; memory_format: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
