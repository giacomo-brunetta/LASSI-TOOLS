# aten.pixel_unshuffle

- Status: ❌ Unsupported
- Error: pixel_unshuffle expects input to have at least 3 dimensions, but got input with 2 dimension(s)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=pixel_unshuffle expects input to have at least 3 dimensions, but got input with 2 dimension(s)
  spec=self: shape=(2, 3) dtype=float32; downscale_factor: 1
- `int32_default`: unsupported; dtype=int32; error=pixel_unshuffle expects input to have at least 3 dimensions, but got input with 2 dimension(s)
  spec=self: shape=(2, 3) dtype=int32; downscale_factor: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
