# aten.bincount

- Status: ❌ Unsupported
- Error: "bincount_cpu" not implemented for 'Float'

## Attempts

- `float32_default`: unsupported; dtype=float32; error="bincount_cpu" not implemented for 'Float'
  spec=self: shape=(2, 3) dtype=float32; weights: shape=(2, 3) dtype=float32; minlength: 1
- `int32_default`: unsupported; dtype=int32; error=bincount only supports 1-d non-negative integral inputs.
  spec=self: shape=(2, 3) dtype=int32; weights: shape=(2, 3) dtype=int32; minlength: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
