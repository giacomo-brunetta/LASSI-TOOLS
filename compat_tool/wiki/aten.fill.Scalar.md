# aten.fill.Scalar

- Status: ❌ Unsupported
- Error: 0 INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/alias_analysis.cpp":615, please report a bug to PyTorch. We don't have an op for aten::full_like but it isn't a special case.  Argument types: Tensor, float,   Candidates: 	aten::full_like(Tensor self, Scalar fill_value, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None, MemoryFormat? memory_format=None) -> Tensor 	aten::full_like.out(Tensor self, Scalar fill_value, *, MemoryFormat? memory_format=None, Tensor(a!) out) -> Tensor(a!)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=0 INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/alias_analysis.cpp":615, please report a bug to PyTorch. We don't have an op for aten::full_like but it isn't a special case.  Argument types: Tensor, float,   Candidates: 	aten::full_like(Tensor self, Scalar fill_value, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None, MemoryFormat? memory_format=None) -> Tensor 	aten::full_like.out(Tensor self, Scalar fill_value, *, MemoryFormat? memory_format=None, Tensor(a!) out) -> Tensor(a!)
  spec=self: shape=(2, 3) dtype=float32; value: 1.0
- `int32_default`: unsupported; dtype=int32; error=0 INTERNAL ASSERT FAILED at "../torch/csrc/jit/ir/alias_analysis.cpp":615, please report a bug to PyTorch. We don't have an op for aten::full_like but it isn't a special case.  Argument types: Tensor, int,   Candidates: 	aten::full_like(Tensor self, Scalar fill_value, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None, MemoryFormat? memory_format=None) -> Tensor 	aten::full_like.out(Tensor self, Scalar fill_value, *, MemoryFormat? memory_format=None, Tensor(a!) out) -> Tensor(a!)
  spec=self: shape=(2, 3) dtype=int32; value: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
