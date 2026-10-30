# aten.nonzero_static

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: Overloaded torch operator invoked from Python failed to many any schema: aten::nonzero_static() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 1 Value: [2, 3] Declaration: aten::nonzero_static(Tensor self, *, int size, int fill_value=-1) -> Tensor Cast error details: Unable to cast Python instance of type <class 'list'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)  aten::nonzero_stati... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
