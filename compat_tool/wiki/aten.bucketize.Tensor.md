# aten.bucketize.Tensor

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; boundaries: shape=(4,) dtype=float32; out_int32: False; right: False
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.greater' op requires the same element type for all operands note: see current operation: %11 = "tosa.greater"(%10, %0) : (tensor<2x3x1xi32>, tensor<4xf32>) -> tensor<2x3x4xi1>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; boundaries: shape=(4,) dtype=float32; out_int32: False; right: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
