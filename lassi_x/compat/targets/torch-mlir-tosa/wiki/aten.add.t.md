# aten.add.t

- Status: ❌ Unsupported
- Error: aten::add() Expected a value of type 'List[t]' for argument 'a' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::add.t(t[] a, t[] b) -> t[] Cast error details: toIValue() cannot handle converting to type: t
- Alternative: Use `aten.add.Tensor` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::add() Expected a value of type 'List[t]' for argument 'a' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::add.t(t[] a, t[] b) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=a: [1]; b: [1]
- `int32_default`: unsupported; dtype=int32; error=aten::add() Expected a value of type 'List[t]' for argument 'a' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::add.t(t[] a, t[] b) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=a: [1]; b: [1]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
