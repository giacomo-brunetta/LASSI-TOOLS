# aten.fake_quantize_per_tensor_affine_cachemask

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::fake_quantize_per_tensor_affine_cachemask() is missing value for argument 'scale'. Declaration: aten::fake_quantize_per_tensor_affine_cachemask(Tensor self, float scale, int zero_point, int quant_min, int quant_max) -> (Tensor output, Tensor mask)  aten::fake_quantize_per_tensor_affine_cachemask() is missing value for argument 'scale'. Declaration: aten::fake_quantize_per_tensor_affine_cachemask.out(Tensor self, float scale, int zero_point, int quant_min, int quant_max, *, Tensor(a!) out0, Tensor(b!) out1) -> (Tensor(a!), Tensor(b!))
