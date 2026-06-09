# aten.frobenius_norm.dim

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.frobenius_norm.dim' that was explicitly marked illegal note: see current operation: %3 = "torch.aten.frobenius_norm.dim"(%arg0, %2, %1) : (!torch.vtensor<[2,3],f32>, !torch.list<int>, !torch.bool) -> !torch.vtensor<[2],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.frobenius_norm.dim' that was explicitly marked illegal note: see current operation: %3 = "torch.aten.frobenius_norm.dim"(%arg0, %2, %1) : (!torch.vtensor<[2,3],f32>, !torch.list<int>, !torch.bool) -> !torch.vtensor<[2],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; dim: 1; keepdim: False
- `int32_default`: unsupported; dtype=int32; error=norm(): input dtype should be either floating point or complex. Got Int instead.
  spec=self: shape=(2, 3) dtype=int32; dim: 1; keepdim: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
