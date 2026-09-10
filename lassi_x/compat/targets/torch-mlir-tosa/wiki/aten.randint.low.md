# aten.randint.low

- Status: ❌ Unsupported
- Error: random_ expects 'from' to be less than 'to', but got from=1 >= to=1

## Attempts

- `float32_default`: unsupported; dtype=float32; error=random_ expects 'from' to be less than 'to', but got from=1 >= to=1
  spec=low: 1; high: 1; size: [2, 3]; dtype: None; layout: None; device: 'cpu'; pin_memory: False
- `int32_default`: unsupported; dtype=int32; error=random_ expects 'from' to be less than 'to', but got from=1 >= to=1
  spec=low: 1; high: 1; size: [2, 3]; dtype: None; layout: None; device: 'cpu'; pin_memory: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
