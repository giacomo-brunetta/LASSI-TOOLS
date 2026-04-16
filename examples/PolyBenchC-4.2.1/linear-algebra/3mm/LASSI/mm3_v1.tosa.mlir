module attributes {torch.debug_module_name = "ThreeMMV1"} {
  func.func @forward(%arg0: tensor<800x1000xf32>, %arg1: tensor<1000x900xf32>, %arg2: tensor<900x1200xf32>, %arg3: tensor<1200x1100xf32>) -> tensor<800x1100xf32> {
    %0 = tosa.reshape %arg0 {new_shape = array<i64: 1, 800, 1000>} : (tensor<800x1000xf32>) -> tensor<1x800x1000xf32>
    %1 = tosa.reshape %arg1 {new_shape = array<i64: 1, 1000, 900>} : (tensor<1000x900xf32>) -> tensor<1x1000x900xf32>
    %2 = tosa.matmul %0, %1 : (tensor<1x800x1000xf32>, tensor<1x1000x900xf32>) -> tensor<1x800x900xf32>
    %3 = tosa.reshape %arg2 {new_shape = array<i64: 1, 900, 1200>} : (tensor<900x1200xf32>) -> tensor<1x900x1200xf32>
    %4 = tosa.reshape %arg3 {new_shape = array<i64: 1, 1200, 1100>} : (tensor<1200x1100xf32>) -> tensor<1x1200x1100xf32>
    %5 = tosa.matmul %3, %4 : (tensor<1x900x1200xf32>, tensor<1x1200x1100xf32>) -> tensor<1x900x1100xf32>
    %6 = tosa.matmul %2, %5 : (tensor<1x800x900xf32>, tensor<1x900x1100xf32>) -> tensor<1x800x1100xf32>
    %7 = tosa.reshape %6 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    return %7 : tensor<800x1100xf32>
  }
}
