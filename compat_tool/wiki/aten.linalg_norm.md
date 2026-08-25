# aten.linalg_norm

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; ord: None; dim: 1; keepdim: False; dtype: None
- `int32_default`: unsupported; dtype=int32; error=linalg.vector_norm: Expected a floating point or complex tensor as input. Got Int
  spec=self: shape=(2, 3) dtype=int32; ord: None; dim: 1; keepdim: False; dtype: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
