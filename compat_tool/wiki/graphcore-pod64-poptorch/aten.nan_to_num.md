# aten.nan_to_num

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; nan: 1.0; posinf: 1.0; neginf: 1.0 | Error: In poptorch/source/ErrorOnUnsupportedAten.cpp:30: 'poptorch_cpp_error': Unsupported ops found in compiled model: [aten::nan_to_num]. Not all operations are supported yet by Graphcore's PyTorch compiler. If you believe any of these should be, please report this message to support@graphcore.ai. Error raised in:   [0] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; nan: 1.0; posinf: 1.0; neginf: 1.0 | Error: In poptorch/source/ErrorOnUnsupportedAten.cpp:30: 'poptorch_cpp_error': Unsupported ops found in compiled model: [aten::nan_to_num]. Not all operations are supported yet by Graphcore's PyTorch compiler. If you believe any of these should be, please report this message to support@graphcore.ai. Error raised in:   [0] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
