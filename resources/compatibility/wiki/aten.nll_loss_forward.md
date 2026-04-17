# aten.nll_loss_forward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::nll_loss_forward() is missing value for argument 'target'. Declaration: aten::nll_loss_forward(Tensor self, Tensor target, Tensor? weight, int reduction, SymInt ignore_index) -> (Tensor output, Tensor total_weight)  aten::nll_loss_forward() is missing value for argument 'target'. Declaration: aten::nll_loss_forward.output(Tensor self, Tensor target, Tensor? weight, int reduction, SymInt ignore_index, *, Tensor(a!) output, Tensor(b!) total_weight) -> (Tensor(a!), Tensor(b!))
