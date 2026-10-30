# aten.conv_transpose2d.input

- Status: ❌ Unsupported
- Error: aten::conv_transpose2d() Expected a value of type 'List[int]' for argument 'output_padding' but instead found type 'int'. Position: 5 Value: 1 Declaration: aten::conv_transpose2d.input(Tensor input, Tensor weight, Tensor? bias=None, SymInt[2] stride=[1, 1], SymInt[2] padding=[0, 0], SymInt[2] output_padding=[0, 0], SymInt groups=1, SymInt[2] dilation=[1, 1]) -> Tensor  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::conv_transpose2d() Expected a value of type 'List[int]' for argument 'output_padding' but instead found type 'int'. Position: 5 Value: 1 Declaration: aten::conv_transpose2d.input(Tensor input, Tensor weight, Tensor? bias=None, SymInt[2] stride=[1, 1], SymInt[2] padding=[0, 0], SymInt[2] output_padding=[0, 0], SymInt groups=1, SymInt[2] dilation=[1, 1]) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=input: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; bias: None; stride: [1, 1]; padding: [0]; output_padding: 1; groups: 1; dilation: [1, 1]
- `int32_default`: unsupported; dtype=int32; error=aten::conv_transpose2d() Expected a value of type 'List[int]' for argument 'output_padding' but instead found type 'int'. Position: 5 Value: 1 Declaration: aten::conv_transpose2d.input(Tensor input, Tensor weight, Tensor? bias=None, SymInt[2] stride=[1, 1], SymInt[2] padding=[0, 0], SymInt[2] output_padding=[0, 0], SymInt groups=1, SymInt[2] dilation=[1, 1]) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=input: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; bias: None; stride: [1, 1]; padding: [0]; output_padding: 1; groups: 1; dilation: [1, 1]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
