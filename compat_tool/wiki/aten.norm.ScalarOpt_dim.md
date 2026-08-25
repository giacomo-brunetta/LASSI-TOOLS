# aten.norm.ScalarOpt_dim

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; p: 1.0; dim: 1; keepdim: False
- `int32_default`: unsupported; dtype=int32; error=norm(): input dtype should be either floating point or complex. Got Int instead.
  spec=self: shape=(2, 3) dtype=int32; p: 1; dim: 1; keepdim: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
