# aten.ceil.float

- Status: ❌ Unsupported
- Error: Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
- Alternative: Use `aten.ceil` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 1.0
- `int32_default`: unsupported; dtype=int32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
