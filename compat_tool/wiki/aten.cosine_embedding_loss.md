# aten.cosine_embedding_loss

- Status: ❌ Unsupported
- Error: 0D or 1D target tensor expected, multi-target not supported

## Attempts

- `float32_default`: unsupported; dtype=float32; error=0D or 1D target tensor expected, multi-target not supported
  spec=input1: shape=(2, 3) dtype=float32; input2: shape=(2, 3) dtype=float32; target: shape=(2, 3) dtype=float32; margin: 1.0; reduction: 1
- `int32_default`: unsupported; dtype=int32; error=0D or 1D target tensor expected, multi-target not supported
  spec=input1: shape=(2, 3) dtype=int32; input2: shape=(2, 3) dtype=int32; target: shape=(2, 3) dtype=int32; margin: 1; reduction: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
