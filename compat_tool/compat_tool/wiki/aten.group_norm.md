# aten.group_norm

- Status: ❌ Unsupported
- Error: Expected weight to be a vector of size equal to the number of channels in input, but got weight of shape [2, 3] and input of shape [2, 3]

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Expected weight to be a vector of size equal to the number of channels in input, but got weight of shape [2, 3] and input of shape [2, 3]
  spec=input: shape=(2, 3) dtype=float32; num_groups: 1; weight: shape=(2, 3) dtype=float32; bias: None; eps: 1e-05; cudnn_enabled: False
- `int32_default`: unsupported; dtype=int32; error=Expected weight to be a vector of size equal to the number of channels in input, but got weight of shape [2, 3] and input of shape [2, 3]
  spec=input: shape=(2, 3) dtype=int32; num_groups: 1; weight: shape=(2, 3) dtype=int32; bias: None; eps: 1e-05; cudnn_enabled: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
