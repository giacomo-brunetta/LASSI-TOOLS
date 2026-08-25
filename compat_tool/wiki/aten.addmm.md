# aten.addmm

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; mat1: shape=(2, 4) dtype=float32; mat2: shape=(4, 3) dtype=float32; beta: 1.0; alpha: 1.0
- `int32_default`: unsupported; dtype=int32; error=Lowering TorchScript IR -> Torch Backend IR failed with the following diagnostics: error: found an op that was marked as backend illegal note: see current operation: %1 = "torch.aten.addmm"(%arg0, %arg1, %arg2, %0, %0) : (!torch.vtensor<[2,3],si32>, !torch.vtensor<[2,4],si32>, !torch.vtensor<[4,3],si32>, !torch.int, !torch.int) -> !torch.vtensor<[2,3],si32> note: this is likely due to DecomposeComplexOps being unable to decompose this op   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torchscript-module-to-torch-backend-pipeline{backend-legal-ops=aten.flatten.using_ints,aten.native_layer_norm,aten.linear extra-library=})' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=int32; mat1: shape=(2, 4) dtype=int32; mat2: shape=(4, 3) dtype=int32; beta: 1; alpha: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
