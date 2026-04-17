# aten.native_layer_norm

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::native_layer_norm() is missing value for argument 'normalized_shape'. Declaration: aten::native_layer_norm(Tensor input, SymInt[] normalized_shape, Tensor? weight, Tensor? bias, float eps) -> (Tensor, Tensor, Tensor)  aten::native_layer_norm() is missing value for argument 'normalized_shape'. Declaration: aten::native_layer_norm.out(Tensor input, SymInt[] normalized_shape, Tensor? weight, Tensor? bias, float eps, *, Tensor(a!) out0, Tensor(b!) out1, Tensor(c!) out2) -> (Tensor(a!), Tensor(b!), Tensor(c!))
