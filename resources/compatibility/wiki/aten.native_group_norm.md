# aten.native_group_norm

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::native_group_norm() is missing value for argument 'weight'. Declaration: aten::native_group_norm(Tensor input, Tensor? weight, Tensor? bias, SymInt N, SymInt C, SymInt HxW, int group, float eps) -> (Tensor, Tensor, Tensor)  aten::native_group_norm() is missing value for argument 'weight'. Declaration: aten::native_group_norm.out(Tensor input, Tensor? weight, Tensor? bias, SymInt N, SymInt C, SymInt HxW, int group, float eps, *, Tensor(a!) out0, Tensor(b!) out1, Tensor(c!) out2) -> (Tensor(a!), Tensor(b!), Tensor(c!))
