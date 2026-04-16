module attributes {torch.debug_module_name = "CovarianceMoment"} {
  func.func @forward(%arg0: tensor<100x80xf32>) -> tensor<80x80xf32> {
    %0 = "tosa.const"() <{value = dense<[1, 0]> : tensor<2xi32>}> : () -> tensor<2xi32>
    %1 = "tosa.const"() <{value = dense<0.00999999977> : tensor<1xf32>}> : () -> tensor<1xf32>
    %2 = "tosa.const"() <{value = dense<1.000000e+02> : tensor<1x1xf32>}> : () -> tensor<1x1xf32>
    %3 = "tosa.const"() <{value = dense<0.0101010101> : tensor<1x1xf32>}> : () -> tensor<1x1xf32>
    %4 = tosa.reduce_sum %arg0 {axis = 0 : i32} : (tensor<100x80xf32>) -> tensor<1x80xf32>
    %5 = tosa.reshape %4 {new_shape = array<i64: 80>} : (tensor<1x80xf32>) -> tensor<80xf32>
    %6 = tosa.mul %5, %1 {shift = 0 : i8} : (tensor<80xf32>, tensor<1xf32>) -> tensor<80xf32>
    %7 = tosa.transpose %arg0, %0 : (tensor<100x80xf32>, tensor<2xi32>) -> tensor<80x100xf32>
    %8 = tosa.reshape %7 {new_shape = array<i64: 1, 80, 100>} : (tensor<80x100xf32>) -> tensor<1x80x100xf32>
    %9 = tosa.reshape %arg0 {new_shape = array<i64: 1, 100, 80>} : (tensor<100x80xf32>) -> tensor<1x100x80xf32>
    %10 = tosa.matmul %8, %9 : (tensor<1x80x100xf32>, tensor<1x100x80xf32>) -> tensor<1x80x80xf32>
    %11 = tosa.reshape %10 {new_shape = array<i64: 80, 80>} : (tensor<1x80x80xf32>) -> tensor<80x80xf32>
    %12 = tosa.reshape %6 {new_shape = array<i64: 1, 80, 1>} : (tensor<80xf32>) -> tensor<1x80x1xf32>
    %13 = tosa.reshape %6 {new_shape = array<i64: 1, 1, 80>} : (tensor<80xf32>) -> tensor<1x1x80xf32>
    %14 = tosa.matmul %12, %13 : (tensor<1x80x1xf32>, tensor<1x1x80xf32>) -> tensor<1x80x80xf32>
    %15 = tosa.reshape %14 {new_shape = array<i64: 80, 80>} : (tensor<1x80x80xf32>) -> tensor<80x80xf32>
    %16 = tosa.mul %15, %2 {shift = 0 : i8} : (tensor<80x80xf32>, tensor<1x1xf32>) -> tensor<80x80xf32>
    %17 = tosa.sub %11, %16 : (tensor<80x80xf32>, tensor<80x80xf32>) -> tensor<80x80xf32>
    %18 = tosa.mul %17, %3 {shift = 0 : i8} : (tensor<80x80xf32>, tensor<1x1xf32>) -> tensor<80x80xf32>
    return %18 : tensor<80x80xf32>
  }
}
