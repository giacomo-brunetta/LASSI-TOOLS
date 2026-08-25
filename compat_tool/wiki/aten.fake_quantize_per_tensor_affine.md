# aten.fake_quantize_per_tensor_affine

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.round' that was explicitly marked illegal note: see current operation: %10 = "torch.aten.round"(%9) : (!torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.round' that was explicitly marked illegal note: see current operation: %10 = "torch.aten.round"(%9) : (!torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; scale: 1.0; zero_point: 1; quant_min: 1; quant_max: 1
- `int32_default`: unsupported; dtype=int32; error="fake_quantize_tensor_cachemask_kernel_type_handling" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; scale: 1; zero_point: 1; quant_min: 1; quant_max: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
