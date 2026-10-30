# aten.view.dtype

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: self.size(-1) must be divisible by 2 to view Half as Float (different element sizes), but got 3 |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
