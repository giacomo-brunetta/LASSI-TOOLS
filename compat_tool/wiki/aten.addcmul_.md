# aten.addcmul_

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, int32_default

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; tensor1: shape=(2, 3) dtype=float32; tensor2: shape=(2, 3) dtype=float32; value: 1.0
- `int32_default`: supported; dtype=int32; error=None
  spec=self: shape=(2, 3) dtype=int32; tensor1: shape=(2, 3) dtype=int32; tensor2: shape=(2, 3) dtype=int32; value: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
