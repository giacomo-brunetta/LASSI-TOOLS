# aten.repeat_interleave.self_int

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.prims.collapse' that was explicitly marked illegal note: see current operation: %6 = "torch.prims.collapse"(%5, %1, %2) : (!torch.vtensor<[2,3,1],f32>, !torch.int, !torch.int) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.prims.collapse' that was explicitly marked illegal note: see current operation: %6 = "torch.prims.collapse"(%5, %1, %2) : (!torch.vtensor<[2,3,1],f32>, !torch.int, !torch.int) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; repeats: 1; dim: 1; output_size: None
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.prims.collapse' that was explicitly marked illegal note: see current operation: %6 = "torch.prims.collapse"(%5, %1, %2) : (!torch.vtensor<[2,3,1],si32>, !torch.int, !torch.int) -> !torch.vtensor<[2,3],si32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; repeats: 1; dim: 1; output_size: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
