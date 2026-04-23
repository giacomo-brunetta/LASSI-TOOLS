# aten.nan_to_num

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; nan: 1.0; posinf: 1.0; neginf: 1.0
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.to.dtype' that was explicitly marked illegal note: see current operation: %30 = "torch.aten.to.dtype"(%8, %6, %4, %4, %3) : (!torch.vtensor<[],f64>, !torch.int, !torch.bool, !torch.bool, !torch.none) -> !torch.vtensor<[],si32>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; nan: 1; posinf: 1; neginf: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
