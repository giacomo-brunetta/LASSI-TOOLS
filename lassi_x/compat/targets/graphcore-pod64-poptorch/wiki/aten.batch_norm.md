# aten.batch_norm

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(2, 3, 4, 4) dtype=float16; weight: shape=(3,) dtype=float16; bias: None; running_mean: shape=(3,) dtype=float16; running_var: shape=(3,) dtype=float16; training: False; momentum: 1.0; eps: 1e-05; cudnn_enabled: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %44 : Half(2, 3, 4, 4, strides=[48, 16, 4, 1], requires_grad=0, device=ipu:0), %45 : Float(3, strides=[1], requires_grad=0, device=ipu:0), %46 : Float(3, strides=[1], requires_grad=0, device=ipu:0) = aten::native_batch_norm(%7, %15, %40, %23, %31, %48, %49, %50) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791... |
| `fp32` / `canonical` | `compile_rejected` | input: shape=(2, 3, 4, 4) dtype=float32; weight: shape=(3,) dtype=float32; bias: None; running_mean: shape=(3,) dtype=float32; running_var: shape=(3,) dtype=float32; training: False; momentum: 1.0; eps: 1e-05; cudnn_enabled: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %44 : Float(2, 3, 4, 4, strides=[48, 16, 4, 1], requires_grad=0, device=ipu:0), %45 : Float(3, strides=[1], requires_grad=0, device=ipu:0), %46 : Float(3, strides=[1], requires_grad=0, device=ipu:0) = aten::native_batch_norm(%7, %15, %40, %23, %31, %48, %49, %50) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-186179... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
