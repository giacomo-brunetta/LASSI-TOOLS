# aten.log_sigmoid_backward

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.log_sigmoid_backward' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.log_sigmoid_backward"(%arg0, %arg1, %arg2) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
- Range Restriction: Tensor values must be in (0, inf).

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.log_sigmoid_backward' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.log_sigmoid_backward"(%arg0, %arg1, %arg2) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; buffer: shape=(2, 3) dtype=float32
- `float32_domain_(0,inf)`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.log_sigmoid_backward' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.log_sigmoid_backward"(%arg0, %arg1, %arg2) : (!torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>, !torch.vtensor<[2,3],f32>) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=grad_output: shape=(2, 3) dtype=float32; self: shape=(2, 3) dtype=float32; buffer: shape=(2, 3) dtype=float32
  note=Tensor values must be in (0, inf).
- `int32_default`: unsupported; dtype=int32; error="log_sigmoid_backward_cpu" not implemented for 'Int'
  spec=grad_output: shape=(2, 3) dtype=int32; self: shape=(2, 3) dtype=int32; buffer: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
