# aten.log_sigmoid_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::log_sigmoid_backward() is missing value for argument 'self'. Declaration: aten::log_sigmoid_backward(Tensor grad_output, Tensor self, Tensor buffer) -> Tensor  aten::log_sigmoid_backward() is missing value for argument 'self'. Declaration: aten::log_sigmoid_backward.grad_input(Tensor grad_output, Tensor self, Tensor buffer, *, Tensor(a!) grad_input) -> Tensor(a!)
