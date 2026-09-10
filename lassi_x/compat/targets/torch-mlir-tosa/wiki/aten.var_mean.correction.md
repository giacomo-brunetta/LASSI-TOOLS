# aten.var_mean.correction

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; dim: 1; correction: 1.0; keepdim: False
- `int32_default`: unsupported; dtype=int32; error=var_mean only support floating point and complex dtypes
  spec=self: shape=(2, 3) dtype=int32; dim: 1; correction: 1; keepdim: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
