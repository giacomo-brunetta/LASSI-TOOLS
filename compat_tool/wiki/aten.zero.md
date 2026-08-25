# aten.zero

- Status: ❌ Unsupported
- Error: kind_.is_prim() INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/ir.cpp":1199, please report a bug to PyTorch. Only prim ops are allowed to not have a registered operator but aten::zeros_like doesn't have one either. We don't know if this op has side effects.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=kind_.is_prim() INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/ir.cpp":1199, please report a bug to PyTorch. Only prim ops are allowed to not have a registered operator but aten::zeros_like doesn't have one either. We don't know if this op has side effects.
  spec=self: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=kind_.is_prim() INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/ir.cpp":1199, please report a bug to PyTorch. Only prim ops are allowed to not have a registered operator but aten::zeros_like doesn't have one either. We don't know if this op has side effects.
  spec=self: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
