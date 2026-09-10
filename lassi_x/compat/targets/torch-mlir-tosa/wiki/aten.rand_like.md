# aten.rand_like

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.uniform' that was explicitly marked illegal note: see current operation: %17 = "torch.aten.uniform"(%16, %3, %4, %2) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.float, !torch.none) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.uniform' that was explicitly marked illegal note: see current operation: %17 = "torch.aten.uniform"(%16, %3, %4, %2) : (!torch.vtensor<[2,3],f32>, !torch.float, !torch.float, !torch.none) -> !torch.vtensor<[2,3],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; dtype: None; layout: None; device: 'cpu'; pin_memory: False; memory_format: None
- `int32_default`: unsupported; dtype=int32; error="check_uniform_bounds" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; dtype: None; layout: None; device: 'cpu'; pin_memory: False; memory_format: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
