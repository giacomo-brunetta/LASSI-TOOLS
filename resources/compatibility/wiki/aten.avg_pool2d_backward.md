# aten.avg_pool2d_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::avg_pool2d_backward() is missing value for argument 'self'. Declaration: aten::avg_pool2d_backward(Tensor grad_output, Tensor self, int[2] kernel_size, int[2] stride, int[2] padding, bool ceil_mode, bool count_include_pad, int? divisor_override) -> Tensor  aten::avg_pool2d_backward() is missing value for argument 'self'. Declaration: aten::avg_pool2d_backward.grad_input(Tensor grad_output, Tensor self, int[2] kernel_size, int[2] stride, int[2] padding, bool ceil_mode, bool count_include_pad, int? divisor_override, *, Tensor(a!) grad_input) -> Tensor(a!)
