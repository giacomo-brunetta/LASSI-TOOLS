# aten.upsample_bilinear2d

- Status: ❌ Unsupported
- Error: It is expected input_size equals to 4, but got size 2

## Attempts

- `float32_default`: unsupported; dtype=float32; error=It is expected input_size equals to 4, but got size 2
  spec=self: shape=(2, 3) dtype=float32; output_size: [4, 4]; align_corners: False; scales_h: 1.0; scales_w: 1.0
- `int32_default`: unsupported; dtype=int32; error=It is expected input_size equals to 4, but got size 2
  spec=self: shape=(2, 3) dtype=int32; output_size: [4, 4]; align_corners: False; scales_h: 1; scales_w: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
