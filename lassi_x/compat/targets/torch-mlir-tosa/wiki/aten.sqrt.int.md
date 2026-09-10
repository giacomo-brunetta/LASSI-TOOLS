# aten.sqrt.int

- Status: ❌ Unsupported
- Error: Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
- Range Restriction: Tensor values must be in [0, inf).
- Alternative: Use `aten.sqrt` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 1
- `float32_domain_[0,inf)`: unsupported; dtype=float32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 1
  note=Tensor values must be in [0, inf).
- `int32_default`: unsupported; dtype=int32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
