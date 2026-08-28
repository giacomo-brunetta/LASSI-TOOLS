# aten.stack

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | tensors: list[(2, 3), (2, 3)]/float16; dim: 1 | — |
| `fp32` / `canonical` | `compiled` | tensors: list[(2, 3), (2, 3)]/float32; dim: 1 | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
