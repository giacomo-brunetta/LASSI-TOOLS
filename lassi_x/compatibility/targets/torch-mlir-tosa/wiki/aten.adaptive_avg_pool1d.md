# aten.adaptive_avg_pool1d

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.runtime.assert' that was explicitly marked illegal note: see current operation: "torch.runtime.assert"(%2) <{message = "unimplemented: only support cases where input and output size are equal for non-unit output size"}> : (!torch.bool) -> ()   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.runtime.assert' that was explicitly marked illegal note: see current operation: "torch.runtime.assert"(%2) <{message = "unimplemented: only support cases where input and output size are equal for non-unit output size"}> : (!torch.bool) -> ()   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(1, 2, 8) dtype=float32; output_size: [4]
- `int32_default`: unsupported; dtype=int32; error="adaptive_avg_pool2d" not implemented for 'Int'
  spec=self: shape=(1, 2, 8) dtype=int32; output_size: [4]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
