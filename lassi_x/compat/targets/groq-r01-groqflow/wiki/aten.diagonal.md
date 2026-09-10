# aten.diagonal

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; offset: 1; dim1: 0; dim2: 1 | 2026-08-27 23:54:45.954701278 [W:onnxruntime:, graph.cc:3543 CleanUnusedInitializersAndNodeArgs] Removing initializer '/inner/Add_1_output_0'. It is not used by any node and should be removed from the model. 2026-08-27 23:54:45.954729908 [W:onnxruntime:, graph.cc:3543 CleanUnusedInitializersAndNodeArgs] Removing initializer '/inner/Constant_8_output_0'. It is not used by any node and should be removed from the model. [91m Error: [0m[0mYou model contains ONNX operation(s) that are not suppo... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
