module attributes {torch.debug_module_name = "DoitgenCandidateDModule"} {
  func.func @forward(%arg0: tensor<10x8x12xf32>, %arg1: tensor<12x12xf32>) -> tensor<10x8x12xf32> {
    %0 = "tosa.const"() <{value = dense<[1, 0]> : tensor<2xi32>}> : () -> tensor<2xi32>
    %cst = arith.constant dense<[2, 0, 1]> : tensor<3xi32>
    %cst_0 = arith.constant dense<[1, 2, 0]> : tensor<3xi32>
    %1 = tosa.transpose %arg1, %0 : (tensor<12x12xf32>, tensor<2xi32>) -> tensor<12x12xf32>
    %2 = tosa.reshape %1 {new_shape = array<i64: 1, 12, 12>} : (tensor<12x12xf32>) -> tensor<1x12x12xf32>
    %3 = tosa.transpose %arg0, %cst : (tensor<10x8x12xf32>, tensor<3xi32>) -> tensor<12x10x8xf32>
    %4 = tosa.reshape %3 {new_shape = array<i64: 1, 12, 80>} : (tensor<12x10x8xf32>) -> tensor<1x12x80xf32>
    %5 = tosa.matmul %2, %4 : (tensor<1x12x12xf32>, tensor<1x12x80xf32>) -> tensor<1x12x80xf32>
    %6 = tosa.reshape %5 {new_shape = array<i64: 12, 10, 8>} : (tensor<1x12x80xf32>) -> tensor<12x10x8xf32>
    %7 = tosa.transpose %6, %cst_0 : (tensor<12x10x8xf32>, tensor<3xi32>) -> tensor<10x8x12xf32>
    return %7 : tensor<10x8x12xf32>
  }
}
