# aten.int_repr

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.int_repr' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.int_repr"(%arg0) : (!torch.vtensor<[2,3],!torch.quint8>) -> !torch.vtensor<[2,3],ui8>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.int_repr' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.int_repr"(%arg0) : (!torch.vtensor<[2,3],!torch.quint8>) -> !torch.vtensor<[2,3],ui8>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=quint8
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.int_repr' that was explicitly marked illegal note: see current operation: %0 = "torch.aten.int_repr"(%arg0) : (!torch.vtensor<[2,3],!torch.quint8>) -> !torch.vtensor<[2,3],ui8>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=quint8
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
