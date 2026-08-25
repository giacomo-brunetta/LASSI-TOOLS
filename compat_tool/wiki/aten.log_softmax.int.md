# aten.log_softmax.int

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, float32_domain_(0,inf)
- DType Note: Supported with float32 inputs, but the int32 retry failed.
- Range Restriction: Tensor values must be in (0, inf).

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; dim: 1; dtype: None
- `float32_domain_(0,inf)`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; dim: 1; dtype: None
  note=Tensor values must be in (0, inf).
- `int32_default`: unsupported; dtype=int32; error="log_softmax_lastdim_kernel_impl" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; dim: 1; dtype: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
