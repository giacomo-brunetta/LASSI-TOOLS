# aten.zero

- Status: ❌ Unsupported
- Error: kind_.is_prim() INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/ir.cpp":1199, please report a bug to PyTorch. Only prim ops are allowed to not have a registered operator but aten::zeros_like doesn't have one either. We don't know if this op has side effects.
