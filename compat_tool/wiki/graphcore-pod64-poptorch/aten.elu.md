# aten.elu

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | self: shape=(2, 3) dtype=float16; alpha: 1.0; scale: 1.0; input_scale: 1.0 | — |
| `fp32` / `canonical` | `compiled` | self: shape=(2, 3) dtype=float32; alpha: 1.0; scale: 1.0; input_scale: 1.0 | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
