# aten.round.decimals

- Status: ❌ Unsupported
- Error: Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %4 = "torch.operator"(%3, %0) <{name = "aten.round.decimals"}> : (!torch.tensor<[2,3],f32>, !torch.int) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
- Alternative: Use `aten.round` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.operator' that was explicitly marked illegal note: see current operation: %4 = "torch.operator"(%3, %0) <{name = "aten.round.decimals"}> : (!torch.tensor<[2,3],f32>, !torch.int) -> !torch.tensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; decimals: 1
- `int32_default`: unsupported; dtype=int32; error="round_cpu" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; decimals: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
