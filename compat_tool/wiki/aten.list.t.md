# aten.list.t

- Status: ❌ Unsupported
- Error: aten::list() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::list.t(t[] l) -> t[] Cast error details: toIValue() cannot handle converting to type: t

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::list() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::list.t(t[] l) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=l: [1]
- `int32_default`: unsupported; dtype=int32; error=aten::list() Expected a value of type 'List[t]' for argument 'l' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::list.t(t[] l) -> t[] Cast error details: toIValue() cannot handle converting to type: t
  spec=l: [1]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
