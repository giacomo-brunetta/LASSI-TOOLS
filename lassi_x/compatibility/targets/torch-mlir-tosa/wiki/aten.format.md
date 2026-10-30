# aten.format

- Status: ❌ Unsupported
- Error: 0 INTERNAL ASSERT FAILED at "../aten/src/ATen/core/ivalue.h":652, please report a bug to PyTorch. expected int

## Attempts

- `float32_default`: unsupported; dtype=float32; error=0 INTERNAL ASSERT FAILED at "../aten/src/ATen/core/ivalue.h":652, please report a bug to PyTorch. expected int
  spec=self: 'none'
- `int32_default`: unsupported; dtype=int32; error=0 INTERNAL ASSERT FAILED at "../aten/src/ATen/core/ivalue.h":652, please report a bug to PyTorch. expected int
  spec=self: 'none'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
