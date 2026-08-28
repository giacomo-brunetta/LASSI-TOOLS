# aten.slice_scatter

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; src: shape=(2, 3) dtype=float16; dim: 1; start: None; end: None; step: 1 | RuntimeError: self.has_storage() INTERNAL ASSERT FAILED at "../aten/src/ATen/native/TensorShape.cpp":3865, please report a bug to PyTorch.  |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; src: shape=(2, 3) dtype=float32; dim: 1; start: None; end: None; step: 1 | RuntimeError: self.has_storage() INTERNAL ASSERT FAILED at "../aten/src/ATen/native/TensorShape.cpp":3865, please report a bug to PyTorch.  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
