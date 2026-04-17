# aten.fake_quantize_per_channel_affine_cachemask

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::fake_quantize_per_channel_affine_cachemask() is missing value for argument 'scale'. Declaration: aten::fake_quantize_per_channel_affine_cachemask(Tensor self, Tensor scale, Tensor zero_point, int axis, int quant_min, int quant_max) -> (Tensor output, Tensor mask)  aten::fake_quantize_per_channel_affine_cachemask() is missing value for argument 'scale'. Declaration: aten::fake_quantize_per_channel_affine_cachemask.out(Tensor self, Tensor scale, Tensor zero_point, int axis, int quant_min, int quant_max, *, Tensor(a!) out0, Tensor(b!) out1) -> (Tensor(a!), Tensor(b!))
