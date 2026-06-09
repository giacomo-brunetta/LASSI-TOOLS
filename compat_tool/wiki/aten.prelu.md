# aten.prelu

- Status: ❌ Unsupported
- Error: Mismatch of parameter numbers and input channel size. Found parameter numbers = 6 and channel size = 3.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Mismatch of parameter numbers and input channel size. Found parameter numbers = 6 and channel size = 3.
  spec=self: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=Mismatch of parameter numbers and input channel size. Found parameter numbers = 6 and channel size = 3.
  spec=self: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
