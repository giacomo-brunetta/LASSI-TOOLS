# aten.split_with_sizes

- Status: ❌ Unsupported
- Error: aten::split_with_sizes() Expected a value of type 'List[int]' for argument 'split_sizes' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::split_with_sizes(Tensor(a -> *) self, SymInt[] split_sizes, int dim=0) -> Tensor(a)[]  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::split_with_sizes() Expected a value of type 'List[int]' for argument 'split_sizes' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::split_with_sizes(Tensor(a -> *) self, SymInt[] split_sizes, int dim=0) -> Tensor(a)[]  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; split_sizes: 1; dim: 1
- `int32_default`: unsupported; dtype=int32; error=aten::split_with_sizes() Expected a value of type 'List[int]' for argument 'split_sizes' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::split_with_sizes(Tensor(a -> *) self, SymInt[] split_sizes, int dim=0) -> Tensor(a)[]  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; split_sizes: 1; dim: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
