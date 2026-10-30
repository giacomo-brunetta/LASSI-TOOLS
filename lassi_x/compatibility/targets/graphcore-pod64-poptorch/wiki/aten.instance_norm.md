# aten.instance_norm

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(2, 3, 4, 4) dtype=float16; weight: shape=(3,) dtype=float16; bias: None; running_mean: shape=(3,) dtype=float16; running_var: shape=(3,) dtype=float16; use_input_stats: False; momentum: 1.0; eps: 1e-05; cudnn_enabled: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %52 : Half(1, 6, 4, 4, strides=[96, 16, 4, 1], requires_grad=0, device=ipu:0), %53 : Float(6, strides=[1], requires_grad=0, device=ipu:0), %54 : Float(6, strides=[1], requires_grad=0, device=ipu:0) = aten::native_batch_norm(%156, %147, %48, %151, %155, %110, %111, %112) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649... |
| `fp32` / `canonical` | `compile_rejected` | input: shape=(2, 3, 4, 4) dtype=float32; weight: shape=(3,) dtype=float32; bias: None; running_mean: shape=(3,) dtype=float32; running_var: shape=(3,) dtype=float32; use_input_stats: False; momentum: 1.0; eps: 1e-05; cudnn_enabled: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %52 : Float(1, 6, 4, 4, strides=[96, 16, 4, 1], requires_grad=0, device=ipu:0), %53 : Float(6, strides=[1], requires_grad=0, device=ipu:0), %54 : Float(6, strides=[1], requires_grad=0, device=ipu:0) = aten::native_batch_norm(%156, %147, %48, %151, %155, %110, %111, %112) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-22564... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
