# aten.mul.left_t

- Status: ❌ Unsupported
- Error: aten::mul() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::mul.left_t(t[] l, int n) -> t[] Cast error details: toIValue() cannot handle converting to type: t
- Alternative: Use `aten.mul.Tensor` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::mul() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::mul.left_t(t[] l, int n) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=l: [1]; n: 1
- `int32_default`: unsupported; dtype=int32; error=aten::mul() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::mul.left_t(t[] l, int n) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=l: [1]; n: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
