# aten.unique_dim

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; dim: 1; sorted: False; return_inverse: False; return_counts: False | Error: In poptorch/source/dispatch_tracer/TypeInferenceHandler.cpp:33: 'poptorch_cpp_error': Type inference failed for aten::unique_dim because the operator doesn't have an implementation for the Meta backend. |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; dim: 1; sorted: False; return_inverse: False; return_counts: False | Error: In poptorch/source/dispatch_tracer/TypeInferenceHandler.cpp:33: 'poptorch_cpp_error': Type inference failed for aten::unique_dim because the operator doesn't have an implementation for the Meta backend. |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
