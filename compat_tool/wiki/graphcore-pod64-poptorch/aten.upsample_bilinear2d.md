# aten.upsample_bilinear2d

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8, 8) dtype=float16; output_size: [8, 8]; align_corners: False; scales_h: 1.0; scales_w: 1.0 | Error: In poptorch/popart_compiler/source/CodeletsCompilation.cpp:29: 'poptorch_cpp_error': Could not obtain an exclusive lock on file /home/gbrun/venvs/graphcore/poptorch33_compat/lib/python3.8/site-packages/poptorch/UpsampleBilinear2dCodelets.inc.cpp Error raised in:   [0] CompileCustomCodeletIfNeeded   [1] popart::Session::prepareDevice: Poplar compilation   [2] Compiler::compileAndPrepareDevice   [3] LowerToPopart::compile   [4] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8, 8) dtype=float32; output_size: [8, 8]; align_corners: False; scales_h: 1.0; scales_w: 1.0 | Error: In poptorch/popart_compiler/source/CodeletsCompilation.cpp:29: 'poptorch_cpp_error': Could not obtain an exclusive lock on file /home/gbrun/venvs/graphcore/poptorch33_compat/lib/python3.8/site-packages/poptorch/UpsampleBilinear2dCodelets.inc.cpp Error raised in:   [0] CompileCustomCodeletIfNeeded   [1] popart::Session::prepareDevice: Poplar compilation   [2] Compiler::compileAndPrepareDevice   [3] LowerToPopart::compile   [4] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
