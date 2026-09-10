# aten.nonzero

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16 | Error: In poptorch/source/dispatch_tracer/RegisterMetaOps.cpp.inc:241: 'poptorch_cpp_error': Operations using aten::nonzero are unsupported because the output shape is determined by the tensor values. The IPU cannot support dynamic output shapes. |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32 | Error: In poptorch/source/dispatch_tracer/RegisterMetaOps.cpp.inc:241: 'poptorch_cpp_error': Operations using aten::nonzero are unsupported because the output shape is determined by the tensor values. The IPU cannot support dynamic output shapes. |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
