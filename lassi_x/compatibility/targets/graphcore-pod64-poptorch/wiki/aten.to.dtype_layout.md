# aten.to.dtype_layout

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; dtype: torch.float32; layout: None; device: 'cpu'; pin_memory: False; non_blocking: False; copy: False; memory_format: 0 | Error: In poptorch/source/dispatch_tracer/RegisterAtenOverloads.cpp:309: 'poptorch_cpp_error': Illegal move to CPU (via `.to("cpu")`) when using the dispatcher. Instead, return this output as an IPU tensor. |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; dtype: torch.float32; layout: None; device: 'cpu'; pin_memory: False; non_blocking: False; copy: False; memory_format: 0 | Error: In poptorch/source/dispatch_tracer/RegisterAtenOverloads.cpp:309: 'poptorch_cpp_error': Illegal move to CPU (via `.to("cpu")`) when using the dispatcher. Instead, return this output as an IPU tensor. |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
