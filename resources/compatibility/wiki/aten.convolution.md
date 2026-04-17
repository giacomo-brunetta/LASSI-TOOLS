# aten.convolution

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::convolution() is missing value for argument 'weight'. Declaration: aten::convolution(Tensor input, Tensor weight, Tensor? bias, SymInt[] stride, SymInt[] padding, SymInt[] dilation, bool transposed, SymInt[] output_padding, SymInt groups) -> Tensor  aten::convolution() is missing value for argument 'weight'. Declaration: aten::convolution.out(Tensor input, Tensor weight, Tensor? bias, SymInt[] stride, SymInt[] padding, SymInt[] dilation, bool transposed, SymInt[] output_padding, SymInt groups, *, Tensor(a!) out) -> Tensor(a!)
