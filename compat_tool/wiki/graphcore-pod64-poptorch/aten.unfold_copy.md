# aten.unfold_copy

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: Overloaded torch operator invoked from Python failed to many any schema: aten::unfold_copy() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold_copy(Tensor self, int dimension, int size, int step) -> Tensor Cast error details: Unable to cast Python instance to C++ type (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)  aten::unfold_copy() Expected a value of type 'int... |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: Overloaded torch operator invoked from Python failed to many any schema: aten::unfold_copy() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold_copy(Tensor self, int dimension, int size, int step) -> Tensor Cast error details: Unable to cast Python instance to C++ type (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)  aten::unfold_copy() Expected a value of type 'int... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
