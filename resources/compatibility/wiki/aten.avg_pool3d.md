# aten.avg_pool3d

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::avg_pool3d() is missing value for argument 'kernel_size'. Declaration: aten::avg_pool3d(Tensor self, int[3] kernel_size, int[3] stride=[], int[3] padding=0, bool ceil_mode=False, bool count_include_pad=True, int? divisor_override=None) -> Tensor  aten::avg_pool3d() is missing value for argument 'kernel_size'. Declaration: aten::avg_pool3d.out(Tensor self, int[3] kernel_size, int[3] stride=[], int[3] padding=0, bool ceil_mode=False, bool count_include_pad=True, int? divisor_override=None, *, Tensor(a!) out) -> Tensor(a!)
