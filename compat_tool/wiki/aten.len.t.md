# aten.len.t

- Status: ❌ Unsupported
- Error: aten::len() Expected a value of type 'List[t]' for argument 'a' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::len.t(t[] a) -> int Cast error details: toIValue() cannot handle converting to type: t

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::len() Expected a value of type 'List[t]' for argument 'a' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::len.t(t[] a) -> int Cast error details: toIValue() cannot handle converting to type: t
  spec=a: [1]
- `int32_default`: unsupported; dtype=int32; error=aten::len() Expected a value of type 'List[t]' for argument 'a' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::len.t(t[] a) -> int Cast error details: toIValue() cannot handle converting to type: t
  spec=a: [1]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
