# aten.embedding_bag.padding_idx

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | TypeError: fixture does not exercise requested dtype float16; effective floating dtypes are ['float32'] |
| `fp32` / `canonical` | `compile_rejected` | weight: shape=(4, 3) dtype=float32; indices: shape=(4,) dtype=int64; offsets: shape=(2,) dtype=int64; scale_grad_by_freq: False; mode: 0; sparse: False; per_sample_weights: None; include_last_offset: False; padding_idx: -1 | Error: In poptorch/source/ErrorOnUnsupportedAten.cpp:30: 'poptorch_cpp_error': Unsupported ops found in compiled model: [aten::_embedding_bag_forward_only]. Not all operations are supported yet by Graphcore's PyTorch compiler. If you believe any of these should be, please report this message to support@graphcore.ai. Error raised in:   [0] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
