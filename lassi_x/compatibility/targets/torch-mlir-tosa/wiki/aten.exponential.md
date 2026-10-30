# aten.exponential

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.uniform' that was explicitly marked illegal note: see current operation: %18 = "torch.aten.uniform"(%17, %4, %5, %3) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.float, !torch.none) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.uniform' that was explicitly marked illegal note: see current operation: %18 = "torch.aten.uniform"(%17, %4, %5, %3) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.float, !torch.none) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; lambd: 1.0; generator: None
- `int32_default`: unsupported; dtype=int32; error=Exponential distribution is a continuous probability distribution. dtype must be a floating point but you specified Int
  spec=self: shape=(2, 3) dtype=int32; lambd: 1; generator: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
