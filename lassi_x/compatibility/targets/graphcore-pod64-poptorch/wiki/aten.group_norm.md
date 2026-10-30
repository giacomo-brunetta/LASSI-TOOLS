# aten.group_norm

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(2, 3, 4, 4) dtype=float16; num_groups: 1; weight: shape=(3,) dtype=float16; bias: None; eps: 1e-05; cudnn_enabled: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %23 : Half(2, 3, 4, 4, strides=[48, 16, 4, 1], requires_grad=0, device=ipu:0), %24 : Half(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0), %25 : Half(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0) = aten::native_group_norm(%7, %15, %17, %27, %28, %29, %30, %31) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-2256... |
| `fp32` / `canonical` | `compile_rejected` | input: shape=(2, 3, 4, 4) dtype=float32; num_groups: 1; weight: shape=(3,) dtype=float32; bias: None; eps: 1e-05; cudnn_enabled: False | Error: In poptorch/source/popart_canonicalization/NormalizationOps.cpp:53: 'poptorch_cpp_error': isNone(*weight) != isNone(*bias) Error raised in:   [0] processing %23 : Float(2, 3, 4, 4, strides=[48, 16, 4, 1], requires_grad=0, device=ipu:0), %24 : Float(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0), %25 : Float(2, 1, strides=[1, 1], requires_grad=0, device=ipu:0) = aten::native_group_norm(%7, %15, %17, %27, %28, %29, %30, %31) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-2... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
