# aten.repeat

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::repeat() Expected a value of type 'List[int]' for argument 'repeats' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::repeat(Tensor self, SymInt[] repeats) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::repeat() Expected a value of type 'List[int]' for argument 'repeats' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::repeat.out(Tensor self, SymInt[] repeats, *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::repeat() Expected a value of type 'List[int]' for argument 'repeats' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::repeat(Tensor self, SymInt[] repeats) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::repeat() Expected a value of type 'List[int]' for argument 'repeats' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::repeat.out(Tensor self, SymInt[] repeats, *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; repeats: 1
- `int32_default`: unsupported; dtype=int32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::repeat() Expected a value of type 'List[int]' for argument 'repeats' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::repeat(Tensor self, SymInt[] repeats) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::repeat() Expected a value of type 'List[int]' for argument 'repeats' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::repeat.out(Tensor self, SymInt[] repeats, *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; repeats: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
