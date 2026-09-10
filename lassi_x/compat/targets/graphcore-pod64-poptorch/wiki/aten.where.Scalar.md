# aten.where.Scalar

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `not_applicable` | condition: shape=(2, 3) dtype=bool; self: 1.0; other: 1.0 | canonical operator inputs do not use floating-point tensors |
| `fp32` / `canonical` | `not_applicable` | condition: shape=(2, 3) dtype=bool; self: 1.0; other: 1.0 | canonical operator inputs do not use floating-point tensors |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
