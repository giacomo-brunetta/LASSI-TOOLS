# aten.bitwise_xor_.Tensor

- Status: ✅ Supported
- Error: None
- Supported Profiles: int32_default
- DType Note: Supported with int32 retry, but not with the default float32 inputs.

## Attempts

- `float32_default`: unsupported; dtype=float32; error="bitwise_xor_cpu" not implemented for 'Float'
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
