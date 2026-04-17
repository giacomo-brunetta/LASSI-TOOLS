# aten.max_pool3d_with_indices

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::max_pool3d_with_indices() is missing value for argument 'kernel_size'. Declaration: aten::max_pool3d_with_indices(Tensor self, int[3] kernel_size, int[3] stride=[], int[3] padding=0, int[3] dilation=1, bool ceil_mode=False) -> (Tensor, Tensor)  aten::max_pool3d_with_indices() is missing value for argument 'kernel_size'. Declaration: aten::max_pool3d_with_indices.out(Tensor self, int[3] kernel_size, int[3] stride=[], int[3] padding=0, int[3] dilation=1, bool ceil_mode=False, *, Tensor(a!) out, Tensor(b!) indices) -> (Tensor(a!), Tensor(b!))
