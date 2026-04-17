# aten.sigmoid_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::sigmoid_backward() is missing value for argument 'output'. Declaration: aten::sigmoid_backward(Tensor grad_output, Tensor output) -> Tensor  aten::sigmoid_backward() is missing value for argument 'output'. Declaration: aten::sigmoid_backward.grad_input(Tensor grad_output, Tensor output, *, Tensor(a!) grad_input) -> Tensor(a!)
