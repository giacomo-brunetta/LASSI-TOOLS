# aten.conv2d

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::conv2d() is missing value for argument 'weight'. Declaration: aten::conv2d(Tensor input, Tensor weight, Tensor? bias=None, SymInt[2] stride=[1, 1], SymInt[2] padding=[0, 0], SymInt[2] dilation=[1, 1], SymInt groups=1) -> Tensor  aten::conv2d() is missing value for argument 'weight'. Declaration: aten::conv2d.padding(Tensor input, Tensor weight, Tensor? bias=None, SymInt[2] stride=[1, 1], str padding="valid", SymInt[2] dilation=[1, 1], SymInt groups=1) -> Tensor
