# aten.tensor.bool

- Status: ❌ Unsupported
- Error: 0 INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/alias_analysis.cpp":615, please report a bug to PyTorch. We don't have an op for aten::fill_ but it isn't a special case.  Argument types: Tensor, bool,   Candidates: 	aten::fill_.Scalar(Tensor(a!) self, Scalar value) -> Tensor(a!) 	aten::fill_.Tensor(Tensor(a!) self, Tensor value) -> Tensor(a!)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=0 INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/alias_analysis.cpp":615, please report a bug to PyTorch. We don't have an op for aten::fill_ but it isn't a special case.  Argument types: Tensor, bool,   Candidates: 	aten::fill_.Scalar(Tensor(a!) self, Scalar value) -> Tensor(a!) 	aten::fill_.Tensor(Tensor(a!) self, Tensor value) -> Tensor(a!)
  spec=t: False; dtype: None; device: 'cpu'; requires_grad: False
- `int32_default`: unsupported; dtype=int32; error=0 INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/alias_analysis.cpp":615, please report a bug to PyTorch. We don't have an op for aten::fill_ but it isn't a special case.  Argument types: Tensor, bool,   Candidates: 	aten::fill_.Scalar(Tensor(a!) self, Scalar value) -> Tensor(a!) 	aten::fill_.Tensor(Tensor(a!) self, Tensor value) -> Tensor(a!)
  spec=t: False; dtype: None; device: 'cpu'; requires_grad: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
