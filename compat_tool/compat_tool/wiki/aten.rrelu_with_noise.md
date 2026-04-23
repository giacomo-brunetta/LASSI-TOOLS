# aten.rrelu_with_noise

- Status: ❌ Unsupported
- Error: Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %9 = "torch.operator"(%7, %8, %0, %0, %1, %2) <{name = "aten.rrelu_with_noise"}> : (!torch.tensor<[2,3],f32>, !torch.tensor<[2,3],f32>, !torch.float, !torch.float, !torch.bool, !torch.none) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %9 = "torch.operator"(%7, %8, %0, %0, %1, %2) <{name = "aten.rrelu_with_noise"}> : (!torch.tensor<[2,3],f32>, !torch.tensor<[2,3],f32>, !torch.float, !torch.float, !torch.bool, !torch.none) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; noise: shape=(2, 3) dtype=float32; lower: 1.0; upper: 1.0; training: False; generator: None
- `int32_default`: unsupported; dtype=int32; error="leaky_relu_cpu" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; noise: shape=(2, 3) dtype=int32; lower: 1; upper: 1; training: False; generator: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
