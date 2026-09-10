# aten.conv2d

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(1, 2, 8, 8) dtype=float16; weight: shape=(4, 2, 3, 3) dtype=float16; bias: None; stride: [1, 1]; padding: [0]; dilation: [1, 1]; groups: 1 | compiler frontend exited without returning a compiled model |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
