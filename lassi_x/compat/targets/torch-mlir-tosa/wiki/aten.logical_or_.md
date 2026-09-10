# aten.logical_or_

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.logical_or' op operand #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xf32>' note: see current operation: %2 = "tosa.logical_or"(%1, %0) : (tensor<2x3xf32>, tensor<2x3xf32>) -> tensor<2x3xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
- Range Restriction: Tensor values must be in (0, inf).

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.logical_or' op operand #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xf32>' note: see current operation: %2 = "tosa.logical_or"(%1, %0) : (tensor<2x3xf32>, tensor<2x3xf32>) -> tensor<2x3xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32
- `float32_domain_(0,inf)`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.logical_or' op operand #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xf32>' note: see current operation: %2 = "tosa.logical_or"(%1, %0) : (tensor<2x3xf32>, tensor<2x3xf32>) -> tensor<2x3xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32
  note=Tensor values must be in (0, inf).
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.logical_or' op operand #0 must be tensor of 1-bit signless integer values, but got 'tensor<2x3xi32>' note: see current operation: %2 = "tosa.logical_or"(%1, %0) : (tensor<2x3xi32>, tensor<2x3xi32>) -> tensor<2x3xi32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
