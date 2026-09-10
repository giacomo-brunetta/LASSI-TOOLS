# aten.view_as_complex

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | TypeError: fixture does not exercise requested dtype float16; effective floating dtypes are ['float32'] |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3, 2) dtype=float32 | Error: In poptorch/source/dispatch_tracer/Tensor.cpp:66: 'poptorch_cpp_error': Unsupported tensor input type from pytorch: ComplexFloat |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
