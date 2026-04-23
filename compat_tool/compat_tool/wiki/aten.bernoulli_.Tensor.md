# aten.bernoulli_.Tensor

- Status: ❌ Unsupported
- Error: Expected p_in >= 0 && p_in <= 1 to be true, but got false.  (Could this error message be improved?  If so, please report an enhancement request to PyTorch.)
- Range Restriction: Tensor values must be in [0, 1].

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Expected p_in >= 0 && p_in <= 1 to be true, but got false.  (Could this error message be improved?  If so, please report an enhancement request to PyTorch.)
  spec=self: shape=(2, 3) dtype=float32; p: shape=(2, 3) dtype=float32; generator: None
- `float32_probability_[0,1]`: unsupported; dtype=float32; error=Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.uniform' that was explicitly marked illegal note: see current operation: %13 = "torch.aten.uniform"(%3, %5, %4, %10) : (!torch.vtensor<[2,3],f64>, !torch.float, !torch.float, !torch.none) -> !torch.vtensor<[2,3],f64>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
  spec=self: shape=(2, 3) dtype=float32; p: shape=(2, 3) dtype=float32; generator: None
  note=Tensor values must be in [0, 1].
- `int32_default`: unsupported; dtype=int32; error="bernoulli_tensor_cpu_p_" not implemented for 'Int'
  spec=self: shape=(2, 3) dtype=int32; p: shape=(2, 3) dtype=int32; generator: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
