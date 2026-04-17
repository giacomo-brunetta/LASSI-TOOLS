# aten.nll_loss_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::nll_loss_backward() is missing value for argument 'self'. Declaration: aten::nll_loss_backward(Tensor grad_output, Tensor self, Tensor target, Tensor? weight, int reduction, SymInt ignore_index, Tensor total_weight) -> Tensor  aten::nll_loss_backward() is missing value for argument 'self'. Declaration: aten::nll_loss_backward.grad_input(Tensor grad_output, Tensor self, Tensor target, Tensor? weight, int reduction, SymInt ignore_index, Tensor total_weight, *, Tensor(a!) grad_input) -> Tensor(a!)
