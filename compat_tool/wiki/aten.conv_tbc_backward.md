# aten.conv_tbc_backward

- Status: ❌ Unsupported
- Error: start (1) + length (2) exceeds dimension size (2).

## Attempts

- `float32_default`: unsupported; dtype=float32; error=start (1) + length (2) exceeds dimension size (2).
  spec=self: shape=(2, 3) dtype=float32; input: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; bias: shape=(2, 3) dtype=float32; pad: 1
- `int32_default`: unsupported; dtype=int32; error=start (1) + length (2) exceeds dimension size (2).
  spec=self: shape=(2, 3) dtype=int32; input: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; bias: shape=(2, 3) dtype=int32; pad: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
