# aten.insert.t

- Status: ❌ Unsupported
- Error: aten::insert() Expected a value of type 'List[t]' for argument 'self' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::insert.t(t[](a!) self, int idx, t(b -> *) el) -> () Cast error details: toIValue() cannot handle converting to type: t

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::insert() Expected a value of type 'List[t]' for argument 'self' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::insert.t(t[](a!) self, int idx, t(b -> *) el) -> () Cast error details: toIValue() cannot handle converting to type: t
  spec=self: [1]; idx: 1; el: nan
- `int32_default`: unsupported; dtype=int32; error=aten::insert() Expected a value of type 'List[t]' for argument 'self' but instead found type 'list'. Position: 0 Value: [1] Declaration: aten::insert.t(t[](a!) self, int idx, t(b -> *) el) -> () Cast error details: toIValue() cannot handle converting to type: t
  spec=self: [1]; idx: 1; el: nan
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
