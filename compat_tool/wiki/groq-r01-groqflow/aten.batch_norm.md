# aten.batch_norm

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | input: shape=(2, 3, 4, 4) dtype=float16; weight: shape=(3,) dtype=float16; bias: None; running_mean: shape=(3,) dtype=float16; running_var: shape=(3,) dtype=float16; training: False; momentum: 1.0; eps: 1e-05; cudnn_enabled: False | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
