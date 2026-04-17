# aten.fake_quantize_per_tensor_affine

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::fake_quantize_per_tensor_affine() is missing value for argument 'scale'. Declaration: aten::fake_quantize_per_tensor_affine(Tensor self, float scale, int zero_point, int quant_min, int quant_max) -> Tensor  aten::fake_quantize_per_tensor_affine() is missing value for argument 'scale'. Declaration: aten::fake_quantize_per_tensor_affine.tensor_qparams(Tensor self, Tensor scale, Tensor zero_point, int quant_min, int quant_max) -> Tensor
