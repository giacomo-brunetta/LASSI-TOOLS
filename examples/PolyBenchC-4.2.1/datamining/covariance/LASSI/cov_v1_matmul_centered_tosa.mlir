module attributes {torch.debug_module_name = "CovarianceMatmul"} {
  func.func @forward(%arg0: tensor<100x80xf32>) -> tensor<80x80xf32> {
    %0 = "tosa.const"() <{value = dense<[1, 0]> : tensor<2xi32>}> : () -> tensor<2xi32>
    %1 = "tosa.const"() <{value = dense<0.00999999977> : tensor<1xf32>}> : () -> tensor<1xf32>
    %2 = "tosa.const"() <{value = dense<0.0101010101> : tensor<1x1xf32>}> : () -> tensor<1x1xf32>
    %3 = tosa.reduce_sum %arg0 {axis = 0 : i32} : (tensor<100x80xf32>) -> tensor<1x80xf32>
    %4 = tosa.reshape %3 {new_shape = array<i64: 80>} : (tensor<1x80xf32>) -> tensor<80xf32>
    %5 = tosa.mul %4, %1 {shift = 0 : i8} : (tensor<80xf32>, tensor<1xf32>) -> tensor<80xf32>
    %6 = tosa.reshape %5 {new_shape = array<i64: 1, 80>} : (tensor<80xf32>) -> tensor<1x80xf32>
    %7 = tosa.sub %arg0, %6 : (tensor<100x80xf32>, tensor<1x80xf32>) -> tensor<100x80xf32>
    %8 = tosa.transpose %7, %0 : (tensor<100x80xf32>, tensor<2xi32>) -> tensor<80x100xf32>
    %9 = tosa.reshape %8 {new_shape = array<i64: 1, 80, 100>} : (tensor<80x100xf32>) -> tensor<1x80x100xf32>
    %10 = tosa.reshape %7 {new_shape = array<i64: 1, 100, 80>} : (tensor<100x80xf32>) -> tensor<1x100x80xf32>
    %11 = tosa.matmul %9, %10 : (tensor<1x80x100xf32>, tensor<1x100x80xf32>) -> tensor<1x80x80xf32>
    %12 = tosa.reshape %11 {new_shape = array<i64: 80, 80>} : (tensor<1x80x80xf32>) -> tensor<80x80xf32>
    %13 = tosa.mul %12, %2 {shift = 0 : i8} : (tensor<80x80xf32>, tensor<1x1xf32>) -> tensor<80x80xf32>
    return %13 : tensor<80x80xf32>
  }
}
