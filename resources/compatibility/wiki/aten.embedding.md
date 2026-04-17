# aten.embedding

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::embedding() is missing value for argument 'indices'. Declaration: aten::embedding(Tensor weight, Tensor indices, SymInt padding_idx=-1, bool scale_grad_by_freq=False, bool sparse=False) -> Tensor  aten::embedding() is missing value for argument 'indices'. Declaration: aten::embedding.out(Tensor weight, Tensor indices, SymInt padding_idx=-1, bool scale_grad_by_freq=False, bool sparse=False, *, Tensor(a!) out) -> Tensor(a!)
