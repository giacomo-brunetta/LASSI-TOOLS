# aten.repeat_interleave.self_int

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: aten::repeat_interleave() Expected a value of type 'int' for argument 'repeats' but instead found type 'list'. Position: 1 Value: [1, 1] Declaration: aten::repeat_interleave.self_int(Tensor self, SymInt repeats, int? dim=None, *, int? output_size=None) -> Tensor Cast error details: Unable to cast Python instance to C++ type (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details) |
| `fp32` / `canonical` | `needs_fixture` | — | RuntimeError: aten::repeat_interleave() Expected a value of type 'int' for argument 'repeats' but instead found type 'list'. Position: 1 Value: [1, 1] Declaration: aten::repeat_interleave.self_int(Tensor self, SymInt repeats, int? dim=None, *, int? output_size=None) -> Tensor Cast error details: Unable to cast Python instance to C++ type (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details) |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
