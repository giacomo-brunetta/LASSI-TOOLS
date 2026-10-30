# aten.adaptive_max_pool1d

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8) dtype=float16; output_size: [4] | RuntimeError: Expected out tensor to have dtype long int, but got int instead |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8) dtype=float32; output_size: [4] | RuntimeError: Expected out tensor to have dtype long int, but got int instead |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
