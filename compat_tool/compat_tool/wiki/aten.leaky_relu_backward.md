# aten.leaky_relu_backward

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; negative_slope: 1.0; self_is_result: False
- `int32_default`: unsupported; dtype=int32; error="leaky_relu_backward_cpu" not implemented for 'Int'
  spec=grad_output: shape=(2, 3) dtype=int32; self: shape=(2, 3) dtype=int32; negative_slope: 1; self_is_result: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
