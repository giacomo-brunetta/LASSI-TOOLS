# aten.avg_pool3d_backward

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.avg_pool3d_backward' that was explicitly marked illegal note: see current operation: %6 = "torch.aten.avg_pool3d_backward"(%arg0, %arg1, %4, %4, %5, %2, %2, %3) : (!torch.vtensor<[1,2,6,6,6],f32>, !torch.vtensor<[1,2,6,6,6],f32>, !torch.list<int>, !torch.list<int>, !torch.list<int>, !torch.bool, !torch.bool, !torch.none) -> !torch.vtensor<[1,2,6,6,6],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.avg_pool3d_backward' that was explicitly marked illegal note: see current operation: %6 = "torch.aten.avg_pool3d_backward"(%arg0, %arg1, %4, %4, %5, %2, %2, %3) : (!torch.vtensor<[1,2,6,6,6],f32>, !torch.vtensor<[1,2,6,6,6],f32>, !torch.list<int>, !torch.list<int>, !torch.list<int>, !torch.bool, !torch.bool, !torch.none) -> !torch.vtensor<[1,2,6,6,6],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=grad_output: shape=(1, 2, 6, 6, 6) dtype=float32; self: shape=(1, 2, 6, 6, 6) dtype=float32; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; ceil_mode: False; count_include_pad: False; divisor_override: None
- `int32_default`: unsupported; dtype=int32; error="avg_pool3d_backward_out_frame" not implemented for 'Int'
  spec=grad_output: shape=(1, 2, 6, 6, 6) dtype=int32; self: shape=(1, 2, 6, 6, 6) dtype=int32; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; ceil_mode: False; count_include_pad: False; divisor_override: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
