# aten.view_copy

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::view_copy() is missing value for argument 'size'. Declaration: aten::view_copy(Tensor self, SymInt[] size) -> Tensor  aten::view_copy() is missing value for argument 'size'. Declaration: aten::view_copy.out(Tensor self, SymInt[] size, *, Tensor(a!) out) -> Tensor(a!)  aten::view_copy() is missing value for argument 'dtype'. Declaration: aten::view_copy.dtype_out(Tensor self, ScalarType dtype, *, Tensor(a!) out) -> Tensor(a!)  aten::view_copy() is missing value for argument 'dtype'. Declaration: aten::view_copy.dtype(Tensor self, ScalarType dtype) -> Tensor
