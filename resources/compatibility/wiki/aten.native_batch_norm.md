# aten.native_batch_norm

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::native_batch_norm() is missing value for argument 'weight'. Declaration: aten::native_batch_norm(Tensor input, Tensor? weight, Tensor? bias, Tensor? running_mean, Tensor? running_var, bool training, float momentum, float eps) -> (Tensor, Tensor, Tensor)  aten::native_batch_norm() is missing value for argument 'weight'. Declaration: aten::native_batch_norm.out(Tensor input, Tensor? weight, Tensor? bias, Tensor? running_mean, Tensor? running_var, bool training, float momentum, float eps, *, Tensor(a!) out, Tensor(b!) save_mean, Tensor(c!) save_invstd) -> (Tensor(a!), Tensor(b!), Tensor(c!))
