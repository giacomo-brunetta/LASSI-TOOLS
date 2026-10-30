# aten.nll_loss_forward

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: 0D or 1D target tensor expected, multi-target not supported |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
