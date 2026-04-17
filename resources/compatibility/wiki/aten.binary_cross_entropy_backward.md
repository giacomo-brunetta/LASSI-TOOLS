# aten.binary_cross_entropy_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::binary_cross_entropy_backward() is missing value for argument 'self'. Declaration: aten::binary_cross_entropy_backward(Tensor grad_output, Tensor self, Tensor target, Tensor? weight=None, int reduction=1) -> Tensor  aten::binary_cross_entropy_backward() is missing value for argument 'self'. Declaration: aten::binary_cross_entropy_backward.grad_input(Tensor grad_output, Tensor self, Tensor target, Tensor? weight=None, int reduction=1, *, Tensor(a!) grad_input) -> Tensor(a!)
