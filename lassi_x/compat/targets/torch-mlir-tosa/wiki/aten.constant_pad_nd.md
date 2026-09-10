# aten.constant_pad_nd

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::constant_pad_nd() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::constant_pad_nd(Tensor self, SymInt[] pad, Scalar value=0) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::constant_pad_nd() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::constant_pad_nd.out(Tensor self, SymInt[] pad, Scalar value=0, *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::constant_pad_nd() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::constant_pad_nd(Tensor self, SymInt[] pad, Scalar value=0) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::constant_pad_nd() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::constant_pad_nd.out(Tensor self, SymInt[] pad, Scalar value=0, *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; pad: 1; value: 1.0
- `int32_default`: unsupported; dtype=int32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::constant_pad_nd() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::constant_pad_nd(Tensor self, SymInt[] pad, Scalar value=0) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::constant_pad_nd() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::constant_pad_nd.out(Tensor self, SymInt[] pad, Scalar value=0, *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; pad: 1; value: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
