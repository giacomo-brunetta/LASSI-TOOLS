# aten.index_put

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: shape mismatch: value tensor of shape [2, 3] cannot be broadcast to indexing result of shape [3] |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: shape mismatch: value tensor of shape [2, 3] cannot be broadcast to indexing result of shape [3] |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
