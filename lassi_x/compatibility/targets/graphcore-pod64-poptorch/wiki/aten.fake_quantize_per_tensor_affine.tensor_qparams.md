# aten.fake_quantize_per_tensor_affine.tensor_qparams

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: a Tensor with 6 elements cannot be converted to Scalar |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: a Tensor with 6 elements cannot be converted to Scalar |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
