# aten.avg_pool2d

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::avg_pool2d() is missing value for argument 'kernel_size'. Declaration: aten::avg_pool2d(Tensor self, int[2] kernel_size, int[2] stride=[], int[2] padding=0, bool ceil_mode=False, bool count_include_pad=True, int? divisor_override=None) -> Tensor  aten::avg_pool2d() is missing value for argument 'kernel_size'. Declaration: aten::avg_pool2d.out(Tensor self, int[2] kernel_size, int[2] stride=[], int[2] padding=0, bool ceil_mode=False, bool count_include_pad=True, int? divisor_override=None, *, Tensor(a!) out) -> Tensor(a!)
