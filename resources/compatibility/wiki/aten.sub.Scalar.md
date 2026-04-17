# aten.sub.Scalar

- Status: ❌ Unsupported
- Error: aten::sub() Expected a value of type 'number' for argument 'other' but instead found type 'Tensor'. Position: 1 Value: tensor([[ 1.2738, -0.4086, -2.2374],         [ 0.9898, -2.5593, -1.3031]]) Declaration: aten::sub.Scalar(Tensor self, Scalar other, Scalar alpha=1) -> Tensor Cast error details: Cannot cast tensor([[ 1.2738, -0.4086, -2.2374],         [ 0.9898, -2.5593, -1.3031]]) to number
