# aten.tile

- Status: ❌ Unsupported
- Error: aten::tile() Expected a value of type 'List[int]' for argument 'dims' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::tile(Tensor self, SymInt[] dims) -> Tensor  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::tile() Expected a value of type 'List[int]' for argument 'dims' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::tile(Tensor self, SymInt[] dims) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; dims: 1
- `int32_default`: unsupported; dtype=int32; error=aten::tile() Expected a value of type 'List[int]' for argument 'dims' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::tile(Tensor self, SymInt[] dims) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; dims: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
