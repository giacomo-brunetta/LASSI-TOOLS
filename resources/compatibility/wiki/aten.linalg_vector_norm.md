# aten.linalg_vector_norm

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.linalg_vector_norm' that was explicitly marked illegal note: see current operation: %3 = "torch.aten.linalg_vector_norm"(%arg0, %0, %1, %2, %1) : (!torch.vtensor<[2,3],f32>, !torch.int, !torch.none, !torch.bool, !torch.none) -> !torch.vtensor<[],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
