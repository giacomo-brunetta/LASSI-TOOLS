# aten.avg_pool2d

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tensor.cast' op operand type 'tensor<1x2x8x10xf32>' and result type 'tensor<1x2x8x8xf32>' are cast incompatible note: see current operation: %12 = "tensor.cast"(%11) : (tensor<1x2x8x10xf32>) -> tensor<1x2x8x8xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tensor.cast' op operand type 'tensor<1x2x8x10xf32>' and result type 'tensor<1x2x8x8xf32>' are cast incompatible note: see current operation: %12 = "tensor.cast"(%11) : (tensor<1x2x8x10xf32>) -> tensor<1x2x8x8xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(1, 2, 8, 8) dtype=float32; kernel_size: [1, 1]; stride: [1, 1]; padding: [0]; ceil_mode: False; count_include_pad: False; divisor_override: None
- `int32_default`: unsupported; dtype=int32; error="avg_pool2d" not implemented for 'Int'
  spec=self: shape=(1, 2, 8, 8) dtype=int32; kernel_size: [1, 1]; stride: [1, 1]; padding: [0]; ceil_mode: False; count_include_pad: False; divisor_override: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
