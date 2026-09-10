# aten.adaptive_max_pool3d

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.adaptive_max_pool3d' that was explicitly marked illegal note: see current operation: %2:2 = "torch.aten.adaptive_max_pool3d"(%arg0, %1) : (!torch.vtensor<[1,2,6,6,6],f32>, !torch.list<int>) -> (!torch.vtensor<[1,2,4,4,4],f32>, !torch.vtensor<[1,2,4,4,4],si64>)   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.adaptive_max_pool3d' that was explicitly marked illegal note: see current operation: %2:2 = "torch.aten.adaptive_max_pool3d"(%arg0, %1) : (!torch.vtensor<[1,2,6,6,6],f32>, !torch.list<int>) -> (!torch.vtensor<[1,2,4,4,4],f32>, !torch.vtensor<[1,2,4,4,4],si64>)   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(1, 2, 6, 6, 6) dtype=float32; output_size: [4, 4, 4]
- `int32_default`: unsupported; dtype=int32; error="adaptive_max_pool3d_cpu" not implemented for 'Int'
  spec=self: shape=(1, 2, 6, 6, 6) dtype=int32; output_size: [4, 4, 4]
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
