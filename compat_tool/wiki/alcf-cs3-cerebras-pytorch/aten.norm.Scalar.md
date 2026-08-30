# aten.norm.Scalar

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; p: 1.0 | RuntimeError: Unimplemented Error:  	/n0/jenkins/node2_large/workspace/pytorch/build-ml_frameworks/torch-mlir/setup_build/cmake_build/tools/torch-mlir/projects/ltc/csrc/base_lazy_backend/generated/shape_inference.cpp:111    std::vector<torch::lazy::Shape> torch::lazy::compute_shape_norm(const at::Tensor&, const c10::Scalar&) |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
