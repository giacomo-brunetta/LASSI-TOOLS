# aten.as_strided

- Status: ❌ Unsupported
- Error: aten::as_strided() Expected a value of type 'List[int]' for argument 'stride' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::as_strided(Tensor(a) self, SymInt[] size, SymInt[] stride, SymInt? storage_offset=None) -> Tensor(a)  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::as_strided() Expected a value of type 'List[int]' for argument 'stride' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::as_strided(Tensor(a) self, SymInt[] size, SymInt[] stride, SymInt? storage_offset=None) -> Tensor(a)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; size: [2, 3]; stride: 1; storage_offset: None
- `int32_default`: unsupported; dtype=int32; error=aten::as_strided() Expected a value of type 'List[int]' for argument 'stride' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::as_strided(Tensor(a) self, SymInt[] size, SymInt[] stride, SymInt? storage_offset=None) -> Tensor(a)  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; size: [2, 3]; stride: 1; storage_offset: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
