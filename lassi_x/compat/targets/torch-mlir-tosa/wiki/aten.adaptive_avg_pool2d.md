# aten.adaptive_avg_pool2d

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(1, 2, 8, 8) dtype=float32; output_size: [4, 4]
- `int32_default`: unsupported; dtype=int32; error="adaptive_avg_pool2d" not implemented for 'Int'
  spec=self: shape=(1, 2, 8, 8) dtype=int32; output_size: [4, 4]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
