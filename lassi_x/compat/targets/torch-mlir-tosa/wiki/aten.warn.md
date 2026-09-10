# aten.warn

- Status: ❌ Unsupported
- Error: warn is implemented directly in the interpreter

## Attempts

- `float32_default`: unsupported; dtype=float32; error=warn is implemented directly in the interpreter
  spec=message: 'none'; stacklevel: 1
- `int32_default`: unsupported; dtype=int32; error=warn is implemented directly in the interpreter
  spec=message: 'none'; stacklevel: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
