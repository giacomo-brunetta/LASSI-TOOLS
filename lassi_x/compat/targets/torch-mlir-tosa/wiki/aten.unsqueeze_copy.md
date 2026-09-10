# aten.unsqueeze_copy

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.unsqueeze_copy' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.unsqueeze_copy"(%arg0, %0) : (!torch.vtensor<[2,3],f32>, !torch.int) -> !torch.vtensor<[2,1,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.unsqueeze_copy' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.unsqueeze_copy"(%arg0, %0) : (!torch.vtensor<[2,3],f32>, !torch.int) -> !torch.vtensor<[2,1,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; dim: 1
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.unsqueeze_copy' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.unsqueeze_copy"(%arg0, %0) : (!torch.vtensor<[2,3],si32>, !torch.int) -> !torch.vtensor<[2,1,3],si32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; dim: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
