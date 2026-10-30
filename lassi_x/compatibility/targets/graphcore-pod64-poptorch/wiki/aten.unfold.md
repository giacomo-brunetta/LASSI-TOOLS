# aten.unfold

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: aten::unfold() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold(Tensor(a) self, int dimension, int size, int step) -> Tensor(a) Cast error details: Unable to cast Python instance to C++ type (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details) |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: aten::unfold() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold(Tensor(a) self, int dimension, int size, int step) -> Tensor(a) Cast error details: Unable to cast Python instance to C++ type (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details) |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
