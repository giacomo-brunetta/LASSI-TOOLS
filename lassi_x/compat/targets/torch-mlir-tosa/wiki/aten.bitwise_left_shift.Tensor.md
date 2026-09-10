# aten.bitwise_left_shift.Tensor

- Status: ❌ Unsupported
- Error: "lshift_cpu" not implemented for 'Float'

## Attempts

- `float32_default`: unsupported; dtype=float32; error="lshift_cpu" not implemented for 'Float'
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.bitwise_left_shift.Tensor' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.bitwise_left_shift.Tensor"(%arg0, %arg1) : (!torch.vtensor<[2,3],si32>, !torch.vtensor<[2,3],si32>) -> !torch.vtensor<[2,3],si32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
