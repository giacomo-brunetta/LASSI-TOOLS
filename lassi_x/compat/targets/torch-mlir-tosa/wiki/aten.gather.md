# aten.gather

- Status: ❌ Unsupported
- Error: gather(): Expected dtype int64 for index

## Attempts

- `float32_default`: unsupported; dtype=float32; error=gather(): Expected dtype int64 for index
  spec=self: shape=(2, 3) dtype=float32; dim: 1; index: shape=(2, 3) dtype=int32; sparse_grad: False
- `int32_default`: unsupported; dtype=int32; error=gather(): Expected dtype int64 for index
  spec=self: shape=(2, 3) dtype=int32; dim: 1; index: shape=(2, 3) dtype=int32; sparse_grad: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
