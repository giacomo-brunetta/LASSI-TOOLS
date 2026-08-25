# aten.reciprocal_

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, float32_domain_nonzero
- DType Note: Supported with float32 inputs, but the int32 retry failed.
- Range Restriction: Tensor values must be non-zero.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32
- `float32_domain_nonzero`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32
  note=Tensor values must be non-zero.
- `int32_default`: unsupported; dtype=int32; error=result type Float can't be cast to the desired output type Int
  spec=self: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
