# aten.binary_cross_entropy_backward

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.binary_cross_entropy_backward' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.binary_cross_entropy_backward"(%arg0, %arg1, %arg2, %arg3, %0) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.int) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.binary_cross_entropy_backward' that was explicitly marked illegal note: see current operation: %1 = "torch.aten.binary_cross_entropy_backward"(%arg0, %arg1, %arg2, %arg3, %0) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.int) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; target: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=float32; reduction: 1
- `int32_default`: unsupported; dtype=int32; error=Found dtype Float but expected Int
  spec=grad_output: shape=(2, 3) dtype=int32; self: shape=(2, 3) dtype=float32; target: shape=(2, 3) dtype=float32; weight: shape=(2, 3) dtype=int32; reduction: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
