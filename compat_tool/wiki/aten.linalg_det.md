# aten.linalg_det

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.linalg_det' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.linalg_det"(%arg0) : (!torch.vtensor<[3,3],f32>) -> !torch.vtensor<[],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.linalg_det' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.linalg_det"(%arg0) : (!torch.vtensor<[3,3],f32>) -> !torch.vtensor<[],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=A: shape=(3, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=linalg.det: Expected a floating point or complex tensor as input. Got Int
  spec=A: shape=(3, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
