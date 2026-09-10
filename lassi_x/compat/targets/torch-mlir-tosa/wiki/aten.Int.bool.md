# aten.Int.bool

- Status: ❌ Unsupported
- Error: Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: False
- `int32_default`: unsupported; dtype=int32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
