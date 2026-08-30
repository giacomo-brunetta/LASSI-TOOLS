# aten.div.Scalar_mode

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; other: 1.0; rounding_mode: 'trunc' | RuntimeError: Unimplemented Error:  	/n0/jenkins/node2_large/workspace/pytorch/build-ml_frameworks/torch-mlir/setup_build/cmake_build/tools/torch-mlir/projects/ltc/csrc/base_lazy_backend/generated/shape_inference.cpp:55    std::vector<torch::lazy::Shape> torch::lazy::compute_shape_div(const at::Tensor&, const c10::Scalar&, std::optional<c10::basic_string_view<char> >) |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
