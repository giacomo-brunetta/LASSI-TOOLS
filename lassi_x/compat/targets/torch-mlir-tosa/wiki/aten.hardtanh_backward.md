# aten.hardtanh_backward

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; min_val: 1.0; max_val: 1.0
- `int32_default`: unsupported; dtype=int32; error="hardshrink_backward_cpu" not implemented for 'Int'
  spec=grad_output: shape=(2, 3) dtype=int32; self: shape=(2, 3) dtype=int32; min_val: 1; max_val: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
