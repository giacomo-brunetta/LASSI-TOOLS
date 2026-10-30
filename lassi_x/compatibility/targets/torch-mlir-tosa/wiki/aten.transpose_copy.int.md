# aten.transpose_copy.int

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.transpose_copy.int' that was explicitly marked illegal note: see current operation: %2 = "torch.aten.transpose_copy.int"(%arg0, %0, %1) : (!torch.vtensor<[2,3],f32>, !torch.int, !torch.int) -> !torch.vtensor<[3,2],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.transpose_copy.int' that was explicitly marked illegal note: see current operation: %2 = "torch.aten.transpose_copy.int"(%arg0, %0, %1) : (!torch.vtensor<[2,3],f32>, !torch.int, !torch.int) -> !torch.vtensor<[3,2],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; dim0: 1; dim1: 0
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.transpose_copy.int' that was explicitly marked illegal note: see current operation: %2 = "torch.aten.transpose_copy.int"(%arg0, %0, %1) : (!torch.vtensor<[2,3],si32>, !torch.int, !torch.int) -> !torch.vtensor<[3,2],si32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; dim0: 1; dim1: 0
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
