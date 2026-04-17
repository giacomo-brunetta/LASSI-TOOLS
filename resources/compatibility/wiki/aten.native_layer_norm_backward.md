# aten.native_layer_norm_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::native_layer_norm_backward() is missing value for argument 'input'. Declaration: aten::native_layer_norm_backward(Tensor grad_out, Tensor input, SymInt[] normalized_shape, Tensor mean, Tensor rstd, Tensor? weight, Tensor? bias, bool[3] output_mask) -> (Tensor, Tensor, Tensor)  aten::native_layer_norm_backward() is missing value for argument 'input'. Declaration: aten::native_layer_norm_backward.out(Tensor grad_out, Tensor input, SymInt[] normalized_shape, Tensor mean, Tensor rstd, Tensor? weight, Tensor? bias, bool[3] output_mask, *, Tensor(a!) out0, Tensor(b!) out1, Tensor(c!) out2) -> (Tensor(a!), Tensor(b!), Tensor(c!))
