# aten.slice.t

- Status: ❌ Unsupported
- Error: aten::slice() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::slice.t(t[] l, int? start=None, int? end=None, int step=1) -> t[] Cast error details: toIValue() cannot handle converting to type: t
- Alternative: Use `aten.slice.Tensor` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::slice() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::slice.t(t[] l, int? start=None, int? end=None, int step=1) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=l: [1]; start: None; end: None; step: 1
- `int32_default`: unsupported; dtype=int32; error=aten::slice() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::slice.t(t[] l, int? start=None, int? end=None, int step=1) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=l: [1]; start: None; end: None; step: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
