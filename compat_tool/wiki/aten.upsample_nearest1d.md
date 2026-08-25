# aten.upsample_nearest1d

- Status: ❌ Unsupported
- Error: It is expected input_size equals to 3, but got size 2

## Attempts

- `float32_default`: unsupported; dtype=float32; error=It is expected input_size equals to 3, but got size 2
  spec=self: shape=(2, 3) dtype=float32; output_size: [4]; scales: 1.0
- `int32_default`: unsupported; dtype=int32; error=It is expected input_size equals to 3, but got size 2
  spec=self: shape=(2, 3) dtype=int32; output_size: [4]; scales: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
