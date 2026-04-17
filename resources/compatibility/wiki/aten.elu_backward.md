# aten.elu_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::elu_backward() is missing value for argument 'alpha'. Declaration: aten::elu_backward(Tensor grad_output, Scalar alpha, Scalar scale, Scalar input_scale, bool is_result, Tensor self_or_result) -> Tensor  aten::elu_backward() is missing value for argument 'alpha'. Declaration: aten::elu_backward.grad_input(Tensor grad_output, Scalar alpha, Scalar scale, Scalar input_scale, bool is_result, Tensor self_or_result, *, Tensor(a!) grad_input) -> Tensor(a!)
