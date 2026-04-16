module attributes {torch.debug_module_name = "DoitgenCandidateBModule"} {
  func.func @forward(%arg0: tensor<10x8x12xf32>, %arg1: tensor<12x12xf32>) -> tensor<10x8x12xf32> {
    %0 = tosa.reshape %arg0 {new_shape = array<i64: 1, 80, 12>} : (tensor<10x8x12xf32>) -> tensor<1x80x12xf32>
    %1 = tosa.reshape %arg1 {new_shape = array<i64: 1, 12, 12>} : (tensor<12x12xf32>) -> tensor<1x12x12xf32>
    %2 = tosa.matmul %0, %1 : (tensor<1x80x12xf32>, tensor<1x12x12xf32>) -> tensor<1x80x12xf32>
    %3 = tosa.reshape %2 {new_shape = array<i64: 10, 8, 12>} : (tensor<1x80x12xf32>) -> tensor<10x8x12xf32>
    return %3 : tensor<10x8x12xf32>
  }
}
