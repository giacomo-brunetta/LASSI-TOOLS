# aten.conv1d

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::conv1d() is missing value for argument 'weight'. Declaration: aten::conv1d(Tensor input, Tensor weight, Tensor? bias=None, SymInt[1] stride=[1], SymInt[1] padding=[0], SymInt[1] dilation=[1], SymInt groups=1) -> Tensor  aten::conv1d() is missing value for argument 'weight'. Declaration: aten::conv1d.padding(Tensor input, Tensor weight, Tensor? bias=None, SymInt[1] stride=[1], str padding="valid", SymInt[1] dilation=[1], SymInt groups=1) -> Tensor
