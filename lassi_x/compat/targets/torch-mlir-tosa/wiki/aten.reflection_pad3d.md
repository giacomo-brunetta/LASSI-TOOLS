# aten.reflection_pad3d

- Status: ❌ Unsupported
- Error: padding size is expected to be 6, but got: 1

## Attempts

- `float32_default`: unsupported; dtype=float32; error=padding size is expected to be 6, but got: 1
  spec=self: shape=(2, 3) dtype=float32; padding: [0]
- `int32_default`: unsupported; dtype=int32; error=padding size is expected to be 6, but got: 1
  spec=self: shape=(2, 3) dtype=int32; padding: [0]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
