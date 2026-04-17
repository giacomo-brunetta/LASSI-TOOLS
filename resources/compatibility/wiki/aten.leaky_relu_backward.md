# aten.leaky_relu_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::leaky_relu_backward() is missing value for argument 'self'. Declaration: aten::leaky_relu_backward(Tensor grad_output, Tensor self, Scalar negative_slope, bool self_is_result) -> Tensor  aten::leaky_relu_backward() is missing value for argument 'self'. Declaration: aten::leaky_relu_backward.grad_input(Tensor grad_output, Tensor self, Scalar negative_slope, bool self_is_result, *, Tensor(a!) grad_input) -> Tensor(a!)
