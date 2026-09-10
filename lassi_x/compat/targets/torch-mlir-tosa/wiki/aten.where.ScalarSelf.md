# aten.where.ScalarSelf

- Status: ❌ Unsupported
- Error: where expected condition to be a boolean tensor, but got a tensor with dtype Float

## Attempts

- `float32_default`: unsupported; dtype=float32; error=where expected condition to be a boolean tensor, but got a tensor with dtype Float
  spec=condition: shape=(2, 3) dtype=float32; self: 1.0; other: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=where expected condition to be a boolean tensor, but got a tensor with dtype Int
  spec=condition: shape=(2, 3) dtype=int32; self: 1; other: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
