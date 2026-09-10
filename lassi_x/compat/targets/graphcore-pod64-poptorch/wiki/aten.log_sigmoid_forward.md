# aten.log_sigmoid_forward

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16 | Error: In poptorch/source/PopartCanonicalization.cpp:223: 'poptorch_cpp_error': The canonicalised JIT node has fewer outputs than the dispatch function. This is only an issue because these outputs are used. Error raised in:   [0] processing %9 : Half(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0), %10 : Half(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0) = aten::log_sigmoid_forward(%7) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79:0... |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32 | Error: In poptorch/source/PopartCanonicalization.cpp:223: 'poptorch_cpp_error': The canonicalised JIT node has fewer outputs than the dispatch function. This is only an issue because these outputs are used. Error raised in:   [0] processing %9 : Float(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0), %10 : Float(2, 3, strides=[3, 1], requires_grad=0, device=ipu:0) = aten::log_sigmoid_forward(%7) # /home/gbrun/Graphcore/workspace/lassi-compat-20260827-225649-1861791/compat_tool/utils.py:79... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
