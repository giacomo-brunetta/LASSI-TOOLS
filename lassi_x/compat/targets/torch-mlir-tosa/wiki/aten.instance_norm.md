# aten.instance_norm

- Status: ❌ Unsupported
- Error: Number of dimensions of repeat dims can not be smaller than number of dimensions of tensor

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Number of dimensions of repeat dims can not be smaller than number of dimensions of tensor
  spec=input: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; bias: None; running_mean: shape=(2, 3) dtype=float32; running_var: shape=(2, 3) dtype=float32; use_input_stats: False; momentum: 1.0; eps: 1e-05; cudnn_enabled: False
- `int32_default`: unsupported; dtype=int32; error=Number of dimensions of repeat dims can not be smaller than number of dimensions of tensor
  spec=input: shape=(2, 3) dtype=int32; weight: shape=(2, 3) dtype=int32; bias: None; running_mean: shape=(2, 3) dtype=int32; running_var: shape=(2, 3) dtype=int32; use_input_stats: False; momentum: 1; eps: 1e-05; cudnn_enabled: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
