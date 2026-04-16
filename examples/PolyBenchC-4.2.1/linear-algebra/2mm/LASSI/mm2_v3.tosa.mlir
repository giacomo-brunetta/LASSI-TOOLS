module attributes {torch.debug_module_name = "TwoMMV3"} {
  func.func @forward(%arg0: tensor<1xf32>, %arg1: tensor<1xf32>, %arg2: tensor<800x1100xf32>, %arg3: tensor<1100x900xf32>, %arg4: tensor<900x1200xf32>, %arg5: tensor<800x1200xf32>) -> tensor<800x1200xf32> {
    %0 = tosa.reshape %arg2 {new_shape = array<i64: 1, 800, 1100>} : (tensor<800x1100xf32>) -> tensor<1x800x1100xf32>
    %1 = tosa.reshape %arg3 {new_shape = array<i64: 1, 1100, 900>} : (tensor<1100x900xf32>) -> tensor<1x1100x900xf32>
    %2 = tosa.matmul %0, %1 : (tensor<1x800x1100xf32>, tensor<1x1100x900xf32>) -> tensor<1x800x900xf32>
    %3 = tosa.reshape %2 {new_shape = array<i64: 800, 900>} : (tensor<1x800x900xf32>) -> tensor<800x900xf32>
    %4 = tosa.reshape %arg0 {new_shape = array<i64: 1, 1>} : (tensor<1xf32>) -> tensor<1x1xf32>
    %5 = tosa.mul %3, %4 {shift = 0 : i8} : (tensor<800x900xf32>, tensor<1x1xf32>) -> tensor<800x900xf32>
    %6 = tosa.reshape %5 {new_shape = array<i64: 1, 800, 900>} : (tensor<800x900xf32>) -> tensor<1x800x900xf32>
    %7 = tosa.reshape %arg4 {new_shape = array<i64: 1, 900, 1200>} : (tensor<900x1200xf32>) -> tensor<1x900x1200xf32>
    %8 = tosa.matmul %6, %7 : (tensor<1x800x900xf32>, tensor<1x900x1200xf32>) -> tensor<1x800x1200xf32>
    %9 = tosa.reshape %8 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %10 = tosa.reshape %arg1 {new_shape = array<i64: 1, 1>} : (tensor<1xf32>) -> tensor<1x1xf32>
    %11 = tosa.mul %10, %arg5 {shift = 0 : i8} : (tensor<1x1xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %12 = tosa.add %9, %11 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    return %12 : tensor<800x1200xf32>
  }
}
