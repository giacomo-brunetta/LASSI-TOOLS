# aten.empty_strided

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::empty_strided() Expected a value of type 'List[int]' for argument 'stride' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::empty_strided(SymInt[] size, SymInt[] stride, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::empty_strided() expected at most 3 argument(s) but received 6 argument(s). Declaration: aten::empty_strided.out(SymInt[] size, SymInt[] stride, *, Tensor(a!) out) -> Tensor(a!)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::empty_strided() Expected a value of type 'List[int]' for argument 'stride' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::empty_strided(SymInt[] size, SymInt[] stride, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::empty_strided() expected at most 3 argument(s) but received 6 argument(s). Declaration: aten::empty_strided.out(SymInt[] size, SymInt[] stride, *, Tensor(a!) out) -> Tensor(a!)
  spec=size: [2, 3]; stride: 1; dtype: None; layout: None; device: 'cpu'; pin_memory: False
- `int32_default`: unsupported; dtype=int32; error=Overloaded torch operator invoked from Python failed to match any schema: aten::empty_strided() Expected a value of type 'List[int]' for argument 'stride' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::empty_strided(SymInt[] size, SymInt[] stride, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor  Python error details: TypeError: 'int' object is not iterable  aten::empty_strided() expected at most 3 argument(s) but received 6 argument(s). Declaration: aten::empty_strided.out(SymInt[] size, SymInt[] stride, *, Tensor(a!) out) -> Tensor(a!)
  spec=size: [2, 3]; stride: 1; dtype: None; layout: None; device: 'cpu'; pin_memory: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
