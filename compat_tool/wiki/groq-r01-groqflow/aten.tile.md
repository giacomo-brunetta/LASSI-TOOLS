# aten.tile

- Target: `groq-r01-groqflow`
- Family: `groq`
- Compiler: `groqflow`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; dims: [0, 1] | 2026-08-28 00:20:34.208242063 [W:onnxruntime:, graph.cc:108 MergeShapeInfo] Error merging shape info for output. '/inner/Concat_output_0' source:{2} target:{3}. Falling back to lenient merge. 2026-08-28 00:20:34.208390971 [W:onnxruntime:, graph.cc:3543 CleanUnusedInitializersAndNodeArgs] Removing initializer '/inner/Expand_output_0'. It is not used by any node and should be removed from the model. 2026-08-28 00:20:34.208399511 [W:onnxruntime:, graph.cc:3543 CleanUnusedInitializersAndNodeArgs]... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
