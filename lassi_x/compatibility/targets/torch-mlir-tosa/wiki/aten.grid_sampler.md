# aten.grid_sampler

- Status: ❌ Unsupported
- Error: grid_sampler(): expected grid to have size 0 in last dimension, but got grid with sizes [2, 3]

## Attempts

- `float32_default`: unsupported; dtype=float32; error=grid_sampler(): expected grid to have size 0 in last dimension, but got grid with sizes [2, 3]
  spec=input: shape=(2, 3) dtype=float32; grid: shape=(2, 3) dtype=float32; interpolation_mode: 1; padding_mode: 1; align_corners: False
- `int32_default`: unsupported; dtype=int32; error=grid_sampler(): expected grid to have size 0 in last dimension, but got grid with sizes [2, 3]
  spec=input: shape=(2, 3) dtype=int32; grid: shape=(2, 3) dtype=int32; interpolation_mode: 1; padding_mode: 1; align_corners: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
