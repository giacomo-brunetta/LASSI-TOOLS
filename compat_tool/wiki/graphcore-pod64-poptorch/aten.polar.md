# aten.polar

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | abs: shape=(2, 3) dtype=float16; angle: shape=(2, 3) dtype=float16 | Error: In poptorch/source/dispatch_tracer/Tensor.cpp:66: 'poptorch_cpp_error': Unsupported tensor input type from pytorch: ComplexHalf |
| `fp32` / `canonical` | `compile_rejected` | abs: shape=(2, 3) dtype=float32; angle: shape=(2, 3) dtype=float32 | Error: In poptorch/source/dispatch_tracer/Tensor.cpp:66: 'poptorch_cpp_error': Unsupported tensor input type from pytorch: ComplexFloat |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
