# aten.avg_pool3d

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 6, 6, 6) dtype=float16; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; ceil_mode: False; count_include_pad: False; divisor_override: None | Error: In unknown:0: 'popart_exception': Padding vector (length 2) does not have 2 values for each spatial dimension 3 Error raised in:   [0] processing %46 : FloatTensor = popart::averagepool(%45) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] LowerToPopartImpl::lowerBody   [2] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(1, 2, 6, 6, 6) dtype=float32; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; ceil_mode: False; count_include_pad: False; divisor_override: None | Error: In unknown:0: 'popart_exception': Padding vector (length 2) does not have 2 values for each spatial dimension 3 Error raised in:   [0] processing %45 : Float(1, 2, 6, 6, 6, strides=[432, 216, 36, 6, 1], requires_grad=0, device=ipu:0) = popart::averagepool(%7) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] LowerToPopartImpl::lowerBody   [2] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
