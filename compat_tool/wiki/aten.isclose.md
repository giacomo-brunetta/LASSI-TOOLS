# aten.isclose

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; other: shape=(2, 3) dtype=float32; rtol: 1.0; atol: 1.0; equal_nan: False
- `int32_default`: unsupported; dtype=int32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.isclose' that was explicitly marked illegal note: see current operation: %2 = "torch.aten.isclose"(%arg0, %arg1, %0, %0, %1) : (!torch.vtensor<[2,3],si32>, !torch.vtensor<[2,3],si32>, !torch.float, !torch.float, !torch.bool) -> !torch.vtensor<[2,3],i1>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; other: shape=(2, 3) dtype=int32; rtol: 1; atol: 1; equal_nan: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
