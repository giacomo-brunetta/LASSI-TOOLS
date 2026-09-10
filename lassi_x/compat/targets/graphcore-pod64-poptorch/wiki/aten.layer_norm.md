# aten.layer_norm

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(2, 3) dtype=float16; normalized_shape: [3]; weight: shape=(3,) dtype=float16; bias: None; eps: 1e-05; cudnn_enable: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %20 : Half(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0), %21 : Float(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0), %22 : Float(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0) = aten::native_layer_norm(%7, %25, %15, %18, %27) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/util... |
| `fp32` / `canonical` | `compile_rejected` | input: shape=(2, 3) dtype=float32; normalized_shape: [3]; weight: shape=(3,) dtype=float32; bias: None; eps: 1e-05; cudnn_enable: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %20 : Float(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0), %21 : Float(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0), %22 : Float(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0) = aten::native_layer_norm(%7, %25, %15, %18, %27) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/uti... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
