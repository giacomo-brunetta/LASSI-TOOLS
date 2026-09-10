# aten.device.with_index

- Status: ❌ Unsupported
- Error: isString() INTERNAL ASSERT FAILED at "../aten/src/ATen/core/ivalue_inl.h":2355, please report a bug to PyTorch. Expected String but got Int

## Attempts

- `float32_default`: unsupported; dtype=float32; error=isString() INTERNAL ASSERT FAILED at "../aten/src/ATen/core/ivalue_inl.h":2355, please report a bug to PyTorch. Expected String but got Int
  spec=type: 'none'; index: 1
- `int32_default`: unsupported; dtype=int32; error=isString() INTERNAL ASSERT FAILED at "../aten/src/ATen/core/ivalue_inl.h":2355, please report a bug to PyTorch. Expected String but got Int
  spec=type: 'none'; index: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
