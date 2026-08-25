# aten.elu_backward

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.elu_backward' that was explicitly marked illegal note: see current operation: %2 = "torch.aten.elu_backward"(%arg0, %0, %0, %0, %1, %arg1) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.float, !torch.float, !torch.bool, !torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.elu_backward' that was explicitly marked illegal note: see current operation: %2 = "torch.aten.elu_backward"(%arg0, %0, %0, %0, %1, %arg1) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.float, !torch.float, !torch.bool, !torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=grad_output: shape=(2, 3) dtype=float32; alpha: 1.0; scale: 1.0; input_scale: 1.0; is_result: False; self_or_result: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error="elu_backward_cpu" not implemented for 'Int'
  spec=grad_output: shape=(2, 3) dtype=int32; alpha: 1; scale: 1; input_scale: 1; is_result: False; self_or_result: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
