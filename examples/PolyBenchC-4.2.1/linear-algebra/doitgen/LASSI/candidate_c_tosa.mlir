module attributes {torch.debug_module_name = "DoitgenCandidateCModule"} {
  func.func @forward(%arg0: tensor<10x8x12xf32>, %arg1: tensor<12x12xf32>) -> tensor<?x?x?xf32> {
    %0 = "tosa.const"() <{value = dense<0.000000e+00> : tensor<?x?x?xf32>}> : () -> tensor<?x?x?xf32>
    %1 = tosa.reshape %arg0 {new_shape = array<i64: 80, 1, 12>} : (tensor<10x8x12xf32>) -> tensor<?x?x?xf32>
    %2 = tosa.reshape %arg1 {new_shape = array<i64: 1, 12, 12>} : (tensor<12x12xf32>) -> tensor<1x12x12xf32>
    %3 = tosa.add %2, %0 : (tensor<1x12x12xf32>, tensor<?x?x?xf32>) -> tensor<?x?x?xf32>
    %4 = tosa.matmul %1, %3 : (tensor<?x?x?xf32>, tensor<?x?x?xf32>) -> tensor<?x?x?xf32>
    %5 = tosa.reshape %4 {new_shape = array<i64: 10, 8, 12>} : (tensor<?x?x?xf32>) -> tensor<?x?x?xf32>
    return %5 : tensor<?x?x?xf32>
  }
}
