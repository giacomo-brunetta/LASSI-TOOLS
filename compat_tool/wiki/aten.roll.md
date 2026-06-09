# aten.roll

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::roll() Expected a value of type 'List[int]' for argument 'shifts' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::roll(Tensor self, SymInt[1] shifts, int[1] dims=[]) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::roll() Expected a value of type 'List[int]' for argument 'shifts' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::roll.out(Tensor self, SymInt[1] shifts, int[1] dims=[], *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::roll() Expected a value of type 'List[int]' for argument 'shifts' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::roll(Tensor self, SymInt[1] shifts, int[1] dims=[]) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::roll() Expected a value of type 'List[int]' for argument 'shifts' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::roll.out(Tensor self, SymInt[1] shifts, int[1] dims=[], *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; shifts: 1; dims: 1
- `int32_default`: unsupported; dtype=int32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::roll() Expected a value of type 'List[int]' for argument 'shifts' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::roll(Tensor self, SymInt[1] shifts, int[1] dims=[]) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::roll() Expected a value of type 'List[int]' for argument 'shifts' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::roll.out(Tensor self, SymInt[1] shifts, int[1] dims=[], *, Tensor(a!) out) -> Tensor(a!)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; shifts: 1; dims: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
