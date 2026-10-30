# aten.tile

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; dims: [0, 1] | Error: In unknown:0: 'popart_exception': Need the value of the ai.onnx.Expand:8 input 'shape' to determine the output shape, but was unable because Expand shape constraint: corresponding dimensions must have the same value or one of them must be 1 Error raised in:   [0] popart::InferenceSession::createFromOnnxModel   [1] Compiler::initSession   [2] LowerToPopart::compile   [3] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; dims: [0, 1] | Error: In unknown:0: 'popart_exception': Need the value of the ai.onnx.Expand:8 input 'shape' to determine the output shape, but was unable because Expand shape constraint: corresponding dimensions must have the same value or one of them must be 1 Error raised in:   [0] popart::InferenceSession::createFromOnnxModel   [1] Compiler::initSession   [2] LowerToPopart::compile   [3] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
