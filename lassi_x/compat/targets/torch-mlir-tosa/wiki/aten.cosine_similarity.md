# aten.cosine_similarity

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=x1: shape=(2, 3) dtype=float32; x2: shape=(2, 3) dtype=float32; dim: 1; eps: 1e-05
- `int32_default`: unsupported; dtype=int32; error=expected common dtype to be floating point, yet common dtype is Int
  spec=x1: shape=(2, 3) dtype=int32; x2: shape=(2, 3) dtype=int32; dim: 1; eps: 1e-05
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
