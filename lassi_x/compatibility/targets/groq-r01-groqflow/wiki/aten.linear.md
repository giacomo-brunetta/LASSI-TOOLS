# aten.linear

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | input: shape=(2, 3) dtype=float16; weight: shape=(2, 3) dtype=float16; bias: None | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
