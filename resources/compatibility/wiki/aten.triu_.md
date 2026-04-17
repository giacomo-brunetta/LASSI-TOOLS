# aten.triu_

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: failed to legalize operation 'torch.aten.ge.Tensor' that was explicitly marked illegal note: see current operation: %32 = "torch.aten.ge.Tensor"(%24, %31) : (!torch.vtensor<[1,3],si64>, !torch.vtensor<[2,1],si64>) -> !torch.vtensor<[2,3],i1>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
