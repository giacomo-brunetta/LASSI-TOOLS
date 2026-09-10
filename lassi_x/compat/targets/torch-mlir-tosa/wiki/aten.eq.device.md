# aten.eq.device

- Status: ❌ Unsupported
- Error: Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
- Alternative: Use `aten.eq.Tensor` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 'cpu'; b: 'cpu'
- `int32_default`: unsupported; dtype=int32; error=Only tensors, lists, tuples of tensors, or dictionary of tensors can be output from traced functions
  spec=a: 'cpu'; b: 'cpu'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
