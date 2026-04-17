# aten.arange.start

- Status: ❌ Unsupported
- Error: aten::arange() Expected a value of type 'number' for argument 'start' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.5914,  0.2393, -0.4351],         [ 2.1534,  0.9137,  0.3940]]) Declaration: aten::arange.start(Scalar start, Scalar end, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor Cast error details: Cannot cast tensor([[ 0.5914,  0.2393, -0.4351],         [ 2.1534,  0.9137,  0.3940]]) to number
