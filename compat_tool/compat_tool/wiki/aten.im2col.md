# aten.im2col

- Status: ❌ Unsupported
- Error: It is expected padding equals to 2, but got size 1

## Attempts

- `float32_default`: unsupported; dtype=float32; error=It is expected padding equals to 2, but got size 1
  spec=self: shape=(2, 3) dtype=float32; kernel_size: 1; dilation: 1; padding: [0]; stride: 1
- `int32_default`: unsupported; dtype=int32; error=It is expected padding equals to 2, but got size 1
  spec=self: shape=(2, 3) dtype=int32; kernel_size: 1; dilation: 1; padding: [0]; stride: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
