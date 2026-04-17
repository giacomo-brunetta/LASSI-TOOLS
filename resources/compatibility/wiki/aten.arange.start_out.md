# aten.arange.start_out

- Status: ❌ Unsupported
- Error: aten::arange() Expected a value of type 'number' for argument 'start' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.9590,  2.0628, -0.4952],         [-0.7859, -0.8028, -1.1865]]) Declaration: aten::arange.start_out(Scalar start, Scalar end, Scalar step=1, *, Tensor(a!) out) -> Tensor(a!) Cast error details: Cannot cast tensor([[-0.9590,  2.0628, -0.4952],         [-0.7859, -0.8028, -1.1865]]) to number
