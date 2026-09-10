# aten.gt_.Scalar

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.greater' op result #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xf32>' note: see current operation: %3 = "tosa.greater"(%0, %2) : (tensor<2x3xf32>, tensor<f32>) -> tensor<2x3xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.greater' op result #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xf32>' note: see current operation: %3 = "tosa.greater"(%0, %2) : (tensor<2x3xf32>, tensor<f32>) -> tensor<2x3xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; other: 1.0
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.greater' op result #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xi32>' note: see current operation: %3 = "tosa.greater"(%0, %2) : (tensor<2x3xi32>, tensor<i32>) -> tensor<2x3xi32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; other: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
