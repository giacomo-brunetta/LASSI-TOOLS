# aten.slice.t

- Status: ❌ Unsupported
- Error: aten::slice() Expected a value of type 'List[t]' for argument 'l' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.0631, -0.7535,  0.5184],         [-2.1898, -0.4226,  1.6125]]) Declaration: aten::slice.t(t[] l, int? start=None, int? end=None, int step=1) -> t[] Cast error details: toIValue() cannot handle converting to type: t
