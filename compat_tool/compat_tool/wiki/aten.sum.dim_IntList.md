# aten.sum.dim_IntList

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; dim: 1; keepdim: False; dtype: None
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.reshape' op inferred type(s) 'tensor<2xi32>' are incompatible with return type(s) of operation 'tensor<2xi64>' error: 'tosa.reshape' op failed to infer returned types note: see current operation: %6 = "tosa.reshape"(%5) <{new_shape = array<i64: 2>}> : (tensor<2x1xi32>) -> tensor<2xi64>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; dim: 1; keepdim: False; dtype: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
