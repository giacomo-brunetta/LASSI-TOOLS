# aten.conv_tbc

- Status: ❌ Unsupported
- Error: Input must have 3 dims: time, batch, in_channel

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Input must have 3 dims: time, batch, in_channel
  spec=self: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; bias: shape=(2, 3) dtype=float32; pad: 1
- `int32_default`: unsupported; dtype=int32; error=Input must have 3 dims: time, batch, in_channel
  spec=self: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; bias: shape=(2, 3) dtype=int32; pad: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
