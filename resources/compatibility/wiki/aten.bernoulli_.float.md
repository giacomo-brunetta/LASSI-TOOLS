# aten.bernoulli_.float

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.uniform' that was explicitly marked illegal note: see current operation: %15 = "torch.aten.uniform"(%3, %5, %4, %12) : (!torch.vtensor<[2,3],f64>, !torch.float, !torch.float, !torch.none) -> !torch.vtensor<[2,3],f64>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
