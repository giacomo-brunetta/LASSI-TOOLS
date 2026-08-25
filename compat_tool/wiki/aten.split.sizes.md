# aten.split.sizes

- Status: ❌ Unsupported
- Error: aten::split() Expected a value of type 'List[int]' for argument 'split_size' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::split.sizes(Tensor(a -> *) self, SymInt[] split_size, int dim=0) -> Tensor(a)[]  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::split() Expected a value of type 'List[int]' for argument 'split_size' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::split.sizes(Tensor(a -> *) self, SymInt[] split_size, int dim=0) -> Tensor(a)[]  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; split_size: 1; dim: 1
- `int32_default`: unsupported; dtype=int32; error=aten::split() Expected a value of type 'List[int]' for argument 'split_size' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::split.sizes(Tensor(a -> *) self, SymInt[] split_size, int dim=0) -> Tensor(a)[]  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; split_size: 1; dim: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
