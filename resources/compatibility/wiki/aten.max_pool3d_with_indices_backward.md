# aten.max_pool3d_with_indices_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::max_pool3d_with_indices_backward() is missing value for argument 'self'. Declaration: aten::max_pool3d_with_indices_backward(Tensor grad_output, Tensor self, int[3] kernel_size, int[3] stride, int[3] padding, int[3] dilation, bool ceil_mode, Tensor indices) -> Tensor  aten::max_pool3d_with_indices_backward() is missing value for argument 'self'. Declaration: aten::max_pool3d_with_indices_backward.grad_input(Tensor grad_output, Tensor self, int[3] kernel_size, int[3] stride, int[3] padding, int[3] dilation, bool ceil_mode, Tensor indices, *, Tensor(a!) grad_input) -> Tensor(a!)
