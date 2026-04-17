# aten.any

- Status: ❌ Unsupported
- Error: Lowering Torch Backend IR -> TOSA Backend IR failed with the following diagnostics: error: 'tosa.reduce_any' op inferred type(s) 'tensor<1x3xf32>' are incompatible with return type(s) of operation 'tensor<1x3xi1>' error: 'tosa.reduce_any' op failed to infer returned types note: see current operation: %1 = "tosa.reduce_any"(%0) <{axis = 0 : i32}> : (tensor<2x3xf32>) -> tensor<1x3xi1>   python exception: Failure while executing pass pipeline  For Torch-MLIR developers, the error can be reproduced with: $ torch-mlir-opt -pass-pipeline='builtin.module(torch-backend-to-tosa-backend-pipeline)' /tmp/OpModule.mlir Add '-mlir-print-ir-after-all -mlir-disable-threading' to get the IR dump for debugging purpose.
