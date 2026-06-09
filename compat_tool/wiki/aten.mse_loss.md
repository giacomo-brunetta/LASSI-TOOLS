# aten.mse_loss

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.sum.dim_IntList' that was explicitly marked illegal note: see current operation: %13 = "torch.aten.sum.dim_IntList"(%12, %3, %4, %3) : (!torch.vtensor<[2,3],f32>, !torch.none, !torch.bool, !torch.none) -> !torch.vtensor<[],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.sum.dim_IntList' that was explicitly marked illegal note: see current operation: %13 = "torch.aten.sum.dim_IntList"(%12, %3, %4, %3) : (!torch.vtensor<[2,3],f32>, !torch.none, !torch.bool, !torch.none) -> !torch.vtensor<[],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; target: shape=(2, 3) dtype=float32; reduction: 1
- `int32_default`: unsupported; dtype=int32; error="mse_cpu" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; target: shape=(2, 3) dtype=int32; reduction: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
