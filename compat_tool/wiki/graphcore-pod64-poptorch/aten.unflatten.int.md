# aten.unflatten.int

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: unflatten: Provided sizes [1] don't multiply up to the size of dim 1 (3) in the input tensor |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: unflatten: Provided sizes [1] don't multiply up to the size of dim 1 (3) in the input tensor |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
