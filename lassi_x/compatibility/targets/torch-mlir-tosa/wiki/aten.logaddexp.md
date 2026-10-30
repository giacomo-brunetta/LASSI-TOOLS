# aten.logaddexp

- Status: ❌ Unsupported
- Error: Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %6 = "torch.operator"(%4, %5) <{name = "aten.logaddexp"}> : (!torch.tensor<[2,3],f32>, !torch.tensor<[2,3],f32>) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
- Range Restriction: Tensor values must be in (0, inf).

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %6 = "torch.operator"(%4, %5) <{name = "aten.logaddexp"}> : (!torch.tensor<[2,3],f32>, !torch.tensor<[2,3],f32>) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32
- `float32_domain_(0,inf)`: unsupported; dtype=float32; error=Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %6 = "torch.operator"(%4, %5) <{name = "aten.logaddexp"}> : (!torch.tensor<[2,3],f32>, !torch.tensor<[2,3],f32>) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32
  note=Tensor values must be in (0, inf).
- `int32_default`: unsupported; dtype=int32; error="logaddexp_cpu" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
