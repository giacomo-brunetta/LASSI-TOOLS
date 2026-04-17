# aten.gather

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::gather() is missing value for argument 'dim'. Declaration: aten::gather(Tensor self, int dim, Tensor index, *, bool sparse_grad=False) -> Tensor  aten::gather() is missing value for argument 'dim'. Declaration: aten::gather.out(Tensor self, int dim, Tensor index, *, bool sparse_grad=False, Tensor(a!) out) -> Tensor(a!)  aten::gather() is missing value for argument 'dim'. Declaration: aten::gather.dimname(Tensor self, str dim, Tensor index, *, bool sparse_grad=False) -> Tensor  aten::gather() is missing value for argument 'dim'. Declaration: aten::gather.dimname_out(Tensor self, str dim, Tensor index, *, bool sparse_grad=False, Tensor(a!) out) -> Tensor(a!)
