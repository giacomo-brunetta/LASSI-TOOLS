# aten.div.Tensor_mode

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.div.Tensor_mode' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.div.Tensor_mode"(%arg0, %arg1, %0) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.str) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
- Alternative: Use `aten.div.Tensor` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.div.Tensor_mode' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.div.Tensor_mode"(%arg0, %arg1, %0) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.str) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32; rounding_mode: 'trunc'
- `int32_default`: unsupported; dtype=int32; error=ZeroDivisionError
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32; rounding_mode: 'trunc'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
