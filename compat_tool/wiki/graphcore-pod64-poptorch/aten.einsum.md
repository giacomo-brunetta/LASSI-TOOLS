# aten.einsum

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | TypeError: fixture does not exercise requested dtype float16; effective floating dtypes are ['float32'] |
| `fp32` / `canonical` | `compiled` | equation: 'ij,jk->ik'; tensors: list[(2, 4), (4, 3)]/float32; path: None | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
