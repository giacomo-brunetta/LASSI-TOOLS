# aten.logit_

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.logit' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.logit"(%arg0, %0) : (!torch.vtensor<[2,3],f32>, !torch.float) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
- Range Restriction: Tensor values must be in (0, inf).

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.logit' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.logit"(%arg0, %0) : (!torch.vtensor<[2,3],f32>, !torch.float) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; eps: 1e-05
- `float32_domain_(0,inf)`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.logit' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.logit"(%arg0, %0) : (!torch.vtensor<[2,3],f32>, !torch.float) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; eps: 1e-05
  note=Tensor values must be in (0, inf).
- `int32_default`: unsupported; dtype=int32; error=result type Float can't be cast to the desired output type Int
  spec=self: shape=(2, 3) dtype=int32; eps: 1e-05
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
