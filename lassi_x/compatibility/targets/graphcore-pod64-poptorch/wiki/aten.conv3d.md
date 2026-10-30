# aten.conv3d

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(1, 2, 6, 6, 6) dtype=float16; weight: shape=(4, 2, 3, 3, 3) dtype=float16; bias: None; stride: [1, 1, 1]; padding: [0]; dilation: [1, 1, 1]; groups: 1 | Error: In unknown:0: 'popart_exception': Padding vector (length 2) does not have 2 values for each spatial dimension 3 Error raised in:   [0] processing %52 : Half(1, 4, 4, 4, 4, strides=[256, 64, 16, 4, 1], requires_grad=0, device=ipu:0) = popart::conv(%7, %15) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] LowerToPopartImpl::lowerBody   [2] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | input: shape=(1, 2, 6, 6, 6) dtype=float32; weight: shape=(4, 2, 3, 3, 3) dtype=float32; bias: None; stride: [1, 1, 1]; padding: [0]; dilation: [1, 1, 1]; groups: 1 | Error: In unknown:0: 'popart_exception': Padding vector (length 2) does not have 2 values for each spatial dimension 3 Error raised in:   [0] processing %52 : Float(1, 4, 4, 4, 4, strides=[256, 64, 16, 4, 1], requires_grad=0, device=ipu:0) = popart::conv(%7, %15) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] LowerToPopartImpl::lowerBody   [2] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
