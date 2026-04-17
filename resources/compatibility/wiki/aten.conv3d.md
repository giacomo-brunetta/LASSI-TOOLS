# aten.conv3d

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::conv3d() is missing value for argument 'weight'. Declaration: aten::conv3d(Tensor input, Tensor weight, Tensor? bias=None, SymInt[3] stride=[1, 1, 1], SymInt[3] padding=[0, 0, 0], SymInt[3] dilation=[1, 1, 1], SymInt groups=1) -> Tensor  aten::conv3d() is missing value for argument 'weight'. Declaration: aten::conv3d.padding(Tensor input, Tensor weight, Tensor? bias=None, SymInt[3] stride=[1, 1, 1], str padding="valid", SymInt[3] dilation=[1, 1, 1], SymInt groups=1) -> Tensor
