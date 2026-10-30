# aten.adaptive_avg_pool3d

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 6, 6, 6) dtype=float16; output_size: [4, 4, 4] | Error: In poptorch/source/popart_canonicalization/PoolingOps.cpp:142: 'poptorch_cpp_error': Input dim 0 (6) is not divisible by the corresponding output dim (4). The results will differ numerically from PyTorch's implementation. Error raised in:   [0] processing %10 : Half(1, 2, 4, 4, 4, strides=[128, 64, 16, 4, 1], requires_grad=0, device=ipu:0) = aten::adaptive_avg_pool3d(%7, %15) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] PopartCa... |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(1, 2, 6, 6, 6) dtype=float32; output_size: [4, 4, 4] | Error: In poptorch/source/popart_canonicalization/PoolingOps.cpp:142: 'poptorch_cpp_error': Input dim 0 (6) is not divisible by the corresponding output dim (4). The results will differ numerically from PyTorch's implementation. Error raised in:   [0] processing %10 : Float(1, 2, 4, 4, 4, strides=[128, 64, 16, 4, 1], requires_grad=0, device=ipu:0) = aten::adaptive_avg_pool3d(%7, %15) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] PopartC... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
