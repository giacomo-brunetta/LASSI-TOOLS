# aten.cuda

- Status: ❌ Unsupported
- Error: PyTorch is not linked with support for cuda devices

## Attempts

- `float32_default`: unsupported; dtype=float32; error=PyTorch is not linked with support for cuda devices
  spec=self: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=PyTorch is not linked with support for cuda devices
  spec=self: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
