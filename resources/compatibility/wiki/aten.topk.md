# aten.topk

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::topk() is missing value for argument 'k'. Declaration: aten::topk(Tensor self, SymInt k, int dim=-1, bool largest=True, bool sorted=True) -> (Tensor values, Tensor indices)  aten::topk() is missing value for argument 'k'. Declaration: aten::topk.values(Tensor self, SymInt k, int dim=-1, bool largest=True, bool sorted=True, *, Tensor(a!) values, Tensor(b!) indices) -> (Tensor(a!) values, Tensor(b!) indices)
