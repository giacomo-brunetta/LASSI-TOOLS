# aten.reciprocal

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default, float32_domain_nonzero
- DType Note: Supported with float32 inputs, but the int32 retry failed.
- Range Restriction: Tensor values must be non-zero.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32
- `float32_domain_nonzero`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32
  note=Tensor values must be non-zero.
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.reciprocal' op requires the same element type for all operands and results note: see current operation: %1 = "tosa.reciprocal"(%0) : (tensor<2x3xi32>) -> tensor<2x3xf32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
