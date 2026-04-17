# aten.append.t

- Status: ❌ Unsupported
- Error: aten::append() Expected a value of type 'List[t]' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.5408,  0.0319,  0.4862],         [-1.1555, -0.3260,  0.2556]]) Declaration: aten::append.t(t[](a!) self, t(c -> *) el) -> t[](a!) Cast error details: toIValue() cannot handle converting to type: t
