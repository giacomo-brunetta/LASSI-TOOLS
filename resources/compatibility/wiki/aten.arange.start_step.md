# aten.arange.start_step

- Status: ❌ Unsupported
- Error: aten::arange() Expected a value of type 'number' for argument 'start' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.5010,  1.0439, -1.1044],         [ 0.4769, -0.3472, -0.0898]]) Declaration: aten::arange.start_step(Scalar start, Scalar end, Scalar step=1, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor Cast error details: Cannot cast tensor([[ 0.5010,  1.0439, -1.1044],         [ 0.4769, -0.3472, -0.0898]]) to number
