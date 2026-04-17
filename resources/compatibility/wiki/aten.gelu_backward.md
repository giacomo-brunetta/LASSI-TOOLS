# aten.gelu_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::gelu_backward() is missing value for argument 'self'. Declaration: aten::gelu_backward(Tensor grad_output, Tensor self, *, str approximate="none") -> Tensor  aten::gelu_backward() is missing value for argument 'self'. Declaration: aten::gelu_backward.grad_input(Tensor grad_output, Tensor self, *, str approximate="none", Tensor(a!) grad_input) -> Tensor(a!)
