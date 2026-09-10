# aten.grid_sampler

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: grid_sampler_2d_cpu not implemented for Half |
| `fp32` / `canonical` | `compile_rejected` | input: shape=(1, 2, 4, 4) dtype=float32; grid: shape=(1, 4, 4, 2) dtype=float32; interpolation_mode: 1; padding_mode: 1; align_corners: False | Error: In poptorch/source/ErrorOnUnsupportedAten.cpp:30: 'poptorch_cpp_error': Unsupported ops found in compiled model: [aten::grid_sampler_2d]. Not all operations are supported yet by Graphcore's PyTorch compiler. If you believe any of these should be, please report this message to support@graphcore.ai. Error raised in:   [0] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
