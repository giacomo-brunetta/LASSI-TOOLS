# aten.fake_quantize_per_channel_affine

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; scale: shape=(3,) dtype=float32; zero_point: shape=(3,) dtype=int32; axis: 1; quant_min: 0; quant_max: 255 | RuntimeError: Unimplemented Error:  	/n0/jenkins/node2_large/workspace/pytorch/build-ml_frameworks/torch-mlir/setup_build/cmake_build/tools/torch-mlir/projects/ltc/csrc/base_lazy_backend/generated/shape_inference.cpp:67    std::vector<torch::lazy::Shape> torch::lazy::compute_shape_fake_quantize_per_channel_affine_cachemask(const at::Tensor&, const at::Tensor&, const at::Tensor&, int64_t, int64_t, int64_t) |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
