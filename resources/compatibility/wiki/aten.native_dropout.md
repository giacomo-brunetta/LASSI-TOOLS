# aten.native_dropout

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::native_dropout() is missing value for argument 'p'. Declaration: aten::native_dropout(Tensor input, float p, bool? train) -> (Tensor, Tensor)  aten::native_dropout() is missing value for argument 'p'. Declaration: aten::native_dropout.out(Tensor input, float p, bool? train, *, Tensor(a!) out0, Tensor(b!) out1) -> (Tensor(a!), Tensor(b!))
