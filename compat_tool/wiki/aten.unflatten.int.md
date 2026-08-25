# aten.unflatten.int

- Status: ❌ Unsupported
- Error: aten::unflatten() Expected a value of type 'List[int]' for argument 'sizes' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::unflatten.int(Tensor(a) self, int dim, SymInt[] sizes) -> Tensor(a)  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::unflatten() Expected a value of type 'List[int]' for argument 'sizes' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::unflatten.int(Tensor(a) self, int dim, SymInt[] sizes) -> Tensor(a)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; dim: 1; sizes: 1
- `int32_default`: unsupported; dtype=int32; error=aten::unflatten() Expected a value of type 'List[int]' for argument 'sizes' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::unflatten.int(Tensor(a) self, int dim, SymInt[] sizes) -> Tensor(a)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; dim: 1; sizes: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
