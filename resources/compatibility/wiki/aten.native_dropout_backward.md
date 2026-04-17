# aten.native_dropout_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::native_dropout_backward() is missing value for argument 'mask'. Declaration: aten::native_dropout_backward(Tensor grad_output, Tensor mask, float scale) -> Tensor  aten::native_dropout_backward() is missing value for argument 'mask'. Declaration: aten::native_dropout_backward.out(Tensor grad_output, Tensor mask, float scale, *, Tensor(a!) out) -> Tensor(a!)
