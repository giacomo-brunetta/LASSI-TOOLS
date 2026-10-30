# aten.fake_quantize_per_tensor_affine_cachemask

- Status: ❌ Unsupported
- Error: Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: found an op that was marked as backend illegal note: see current operation: %2:2 = "torch.aten.fake_quantize_per_tensor_affine_cachemask"(%arg0, %0, %1, %1, %1) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.int, !torch.int, !torch.int) -> (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],i1>) note: this is likely due to DecomposeComplexOps being unable to decompose this op   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: found an op that was marked as backend illegal note: see current operation: %2:2 = "torch.aten.fake_quantize_per_tensor_affine_cachemask"(%arg0, %0, %1, %1, %1) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.int, !torch.int, !torch.int) -> (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],i1>) note: this is likely due to DecomposeComplexOps being unable to decompose this op   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; scale: 1.0; zero_point: 1; quant_min: 1; quant_max: 1
- `int32_default`: unsupported; dtype=int32; error="fake_quantize_tensor_cachemask_kernel_type_handling" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; scale: 1; zero_point: 1; quant_min: 1; quant_max: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
