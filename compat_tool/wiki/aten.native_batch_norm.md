# aten.native_batch_norm

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.empty.memory_format' that was explicitly marked illegal note: see current operation: %34 = "torch.aten.empty.memory_format"(%33, %4, %4, %4, %4, %4) : (!torch.list<int>, !torch.none, !torch.none, !torch.none, !torch.none, !torch.none) -> !torch.vtensor<[0],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.empty.memory_format' that was explicitly marked illegal note: see current operation: %34 = "torch.aten.empty.memory_format"(%33, %4, %4, %4, %4, %4) : (!torch.list<int>, !torch.none, !torch.none, !torch.none, !torch.none, !torch.none) -> !torch.vtensor<[0],f32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=input: shape=(2, 3, 4, 4) dtype=float32; weight: shape=(3,) dtype=float32; bias: None; running_mean: shape=(3,) dtype=float32; running_var: shape=(3,) dtype=float32; training: False; momentum: 1.0; eps: 1e-05
- `int32_default`: unsupported; dtype=int32; error="batch_norm" not implemented for 'Int'
  spec=input: shape=(2, 3, 4, 4) dtype=int32; weight: shape=(3,) dtype=int32; bias: None; running_mean: shape=(3,) dtype=int32; running_var: shape=(3,) dtype=int32; training: False; momentum: 1; eps: 1e-05
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
