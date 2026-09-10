# aten.linalg_qr

- Status: ❌ Unsupported
- Error: qr received unrecognized mode 'none' but expected one of 'reduced' (default), 'r', or 'complete'

## Attempts

- `float32_default`: unsupported; dtype=float32; error=qr received unrecognized mode 'none' but expected one of 'reduced' (default), 'r', or 'complete'
  spec=A: shape=(2, 3) dtype=float32; mode: 'none'
- `int32_default`: unsupported; dtype=int32; error=linalg.qr: Expected a floating point or complex tensor as input. Got Int
  spec=A: shape=(2, 3) dtype=int32; mode: 'none'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
