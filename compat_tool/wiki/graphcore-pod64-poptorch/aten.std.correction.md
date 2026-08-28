# aten.std.correction

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; dim: [1]; correction: None; keepdim: False | Error: In poptorch/source/popart_canonicalization/PopartCanonicalizationUtils.cpp:260: 'poptorch_cpp_error': Cannot force a non-constant node to a bool Error raised in:   [0] processing %12 : Half(2, strides=[1], requires_grad=0, device=ipu:0) = aten::std(%7, %15, %10, %17) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] PopartCanonicalization   [2] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; dim: [1]; correction: None; keepdim: False | Error: In poptorch/source/popart_canonicalization/PopartCanonicalizationUtils.cpp:260: 'poptorch_cpp_error': Cannot force a non-constant node to a bool Error raised in:   [0] processing %12 : Float(2, strides=[1], requires_grad=0, device=ipu:0) = aten::std(%7, %15, %10, %17) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] PopartCanonicalization   [2] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
