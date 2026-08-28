# aten.logical_not

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16 | Error: In unknown:0: 'poplar_unknown_vertex_type': Unknown vertex type 'popops::UnaryOp1D<popops::expr::UnaryOpType::LOGICAL_NOT,half> (In addVertex for Compute Set inner/Logical_not/100/Op/LogicalNot).' Error raised in:   [0] popart::Session::prepareDevice: Poplar compilation   [1] Compiler::compileAndPrepareDevice   [2] LowerToPopart::compile   [3] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32 | Error: In unknown:0: 'poplar_unknown_vertex_type': Unknown vertex type 'popops::UnaryOp1D<popops::expr::UnaryOpType::LOGICAL_NOT,float> (In addVertex for Compute Set inner/Logical_not/100/Op/LogicalNot).' Error raised in:   [0] popart::Session::prepareDevice: Poplar compilation   [1] Compiler::compileAndPrepareDevice   [2] LowerToPopart::compile   [3] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
