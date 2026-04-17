# aten.insert.t

- Status: ❌ Unsupported
- Error: aten::insert() Expected a value of type 'List[t]' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.2063,  0.6611,  0.0288],         [-0.0420,  0.9325, -0.7975]]) Declaration: aten::insert.t(t[](a!) self, int idx, t(b -> *) el) -> () Cast error details: toIValue() cannot handle converting to type: t
