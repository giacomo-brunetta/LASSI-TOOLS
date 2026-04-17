# aten.unique_dim

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::unique_dim() is missing value for argument 'dim'. Declaration: aten::unique_dim(Tensor self, int dim, bool sorted=True, bool return_inverse=False, bool return_counts=False) -> (Tensor, Tensor, Tensor)  aten::unique_dim() is missing value for argument 'dim'. Declaration: aten::unique_dim.out(Tensor self, int dim, bool sorted=True, bool return_inverse=False, bool return_counts=False, *, Tensor(a!) out0, Tensor(b!) out1, Tensor(c!) out2) -> (Tensor(a!), Tensor(b!), Tensor(c!))
