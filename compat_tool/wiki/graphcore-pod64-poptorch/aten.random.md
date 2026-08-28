# aten.random

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; generator: None | Error: In unknown:0: 'std::out_of_range': vector::_M_range_check: __n (which is 2) >= this->size() (which is 2) Error raised in:   [0] processing %19 : Half(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0) = aten::random_(%24, %18) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] PopartCanonicalization   [2] compileWithManualTracing  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; generator: None | Error: In unknown:0: 'std::out_of_range': vector::_M_range_check: __n (which is 2) >= this->size() (which is 2) Error raised in:   [0] processing %19 : Float(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0) = aten::random_(%24, %18) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0   [1] PopartCanonicalization   [2] compileWithManualTracing  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
