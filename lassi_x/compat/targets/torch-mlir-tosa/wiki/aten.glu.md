# aten.glu

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 4) dtype=float32; dim: 1
- `int32_default`: unsupported; dtype=int32; error="glu_cpu" not implemented for 'Int'
  spec=self: shape=(2, 4) dtype=int32; dim: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
