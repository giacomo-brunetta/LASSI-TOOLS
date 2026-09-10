# aten.bitwise_or.Tensor

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `not_applicable` | self: shape=(2, 3) dtype=int64; other: shape=(2, 3) dtype=int64 | canonical operator inputs do not use floating-point tensors |
| `fp32` / `canonical` | `not_applicable` | self: shape=(2, 3) dtype=int64; other: shape=(2, 3) dtype=int64 | canonical operator inputs do not use floating-point tensors |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
