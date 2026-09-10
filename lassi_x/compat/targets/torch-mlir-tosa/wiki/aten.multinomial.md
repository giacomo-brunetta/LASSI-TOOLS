# aten.multinomial

- Status: ❌ Unsupported
- Error: probability tensor contains either `inf`, `nan` or element < 0

## Attempts

- `float32_default`: unsupported; dtype=float32; error=probability tensor contains either `inf`, `nan` or element < 0
  spec=self: shape=(2, 3) dtype=float32; num_samples: 1; replacement: False; generator: None
- `int32_default`: unsupported; dtype=int32; error=multinomial only supports floating-point dtypes for input, got: Int
  spec=self: shape=(2, 3) dtype=int32; num_samples: 1; replacement: False; generator: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
