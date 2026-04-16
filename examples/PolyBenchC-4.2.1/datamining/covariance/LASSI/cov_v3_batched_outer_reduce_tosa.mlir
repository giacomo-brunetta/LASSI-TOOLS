module attributes {torch.debug_module_name = "CovarianceBatchedOuter"} {
  func.func @forward(%arg0: tensor<100x80xf32>) -> tensor<80x80xf32> {
    %0 = "tosa.const"() <{value = dense<0.00999999977> : tensor<1xf32>}> : () -> tensor<1xf32>
    %1 = "tosa.const"() <{value = dense<0.0101010101> : tensor<1x1xf32>}> : () -> tensor<1x1xf32>
    %2 = tosa.reduce_sum %arg0 {axis = 0 : i32} : (tensor<100x80xf32>) -> tensor<1x80xf32>
    %3 = tosa.reshape %2 {new_shape = array<i64: 80>} : (tensor<1x80xf32>) -> tensor<80xf32>
    %4 = tosa.mul %3, %0 {shift = 0 : i8} : (tensor<80xf32>, tensor<1xf32>) -> tensor<80xf32>
    %5 = tosa.reshape %4 {new_shape = array<i64: 1, 80>} : (tensor<80xf32>) -> tensor<1x80xf32>
    %6 = tosa.sub %arg0, %5 : (tensor<100x80xf32>, tensor<1x80xf32>) -> tensor<100x80xf32>
    %7 = tosa.reshape %6 {new_shape = array<i64: 100, 80, 1>} : (tensor<100x80xf32>) -> tensor<100x80x1xf32>
    %8 = tosa.reshape %6 {new_shape = array<i64: 100, 1, 80>} : (tensor<100x80xf32>) -> tensor<100x1x80xf32>
    %9 = tosa.mul %7, %8 {shift = 0 : i8} : (tensor<100x80x1xf32>, tensor<100x1x80xf32>) -> tensor<100x80x80xf32>
    %10 = tosa.reduce_sum %9 {axis = 0 : i32} : (tensor<100x80x80xf32>) -> tensor<1x80x80xf32>
    %11 = tosa.reshape %10 {new_shape = array<i64: 80, 80>} : (tensor<1x80x80xf32>) -> tensor<80x80xf32>
    %12 = tosa.mul %11, %1 {shift = 0 : i8} : (tensor<80x80xf32>, tensor<1x1xf32>) -> tensor<80x80xf32>
    return %12 : tensor<80x80xf32>
  }
}
