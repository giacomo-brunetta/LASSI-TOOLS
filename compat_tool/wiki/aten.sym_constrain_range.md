# aten.sym_constrain_range

- Status: ❌ Unsupported
- Error: aten::sym_constrain_range() Expected a value of type 'number' for argument 'size' but instead found type 'list'. Position: 0 Value: [2, 3] Declaration: aten::sym_constrain_range(Scalar size, *, int? min=None, int? max=None) -> () Cast error details: Cannot cast [2, 3] to number

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::sym_constrain_range() Expected a value of type 'number' for argument 'size' but instead found type 'list'. Position: 0 Value: [2, 3] Declaration: aten::sym_constrain_range(Scalar size, *, int? min=None, int? max=None) -> () Cast error details: Cannot cast [2, 3] to number
  spec=size: [2, 3]; min: None; max: None
- `int32_default`: unsupported; dtype=int32; error=aten::sym_constrain_range() Expected a value of type 'number' for argument 'size' but instead found type 'list'. Position: 0 Value: [2, 3] Declaration: aten::sym_constrain_range(Scalar size, *, int? min=None, int? max=None) -> () Cast error details: Cannot cast [2, 3] to number
  spec=size: [2, 3]; min: None; max: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
