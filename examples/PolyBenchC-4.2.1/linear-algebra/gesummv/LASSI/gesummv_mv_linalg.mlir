#map = affine_map<(d0) -> ()>
#map1 = affine_map<(d0) -> (d0)>
module attributes {torch.debug_module_name = "GesummvMv"} {
  ml_program.global private mutable @global_seed(dense<0> : tensor<i64>) : tensor<i64>
  func.func @forward(%arg0: tensor<1300x1300xf32>, %arg1: tensor<1300x1300xf32>, %arg2: tensor<1300xf32>) -> tensor<1300xf32> {
    %cst = arith.constant dense<1.500000e+00> : tensor<f32>
    %cst_0 = arith.constant 0.000000e+00 : f32
    %cst_1 = arith.constant dense<1.200000e+00> : tensor<f32>
    %0 = tensor.empty() : tensor<1300xf32>
    %1 = linalg.fill ins(%cst_0 : f32) outs(%0 : tensor<1300xf32>) -> tensor<1300xf32>
    %2 = linalg.matvec ins(%arg0, %arg2 : tensor<1300x1300xf32>, tensor<1300xf32>) outs(%1 : tensor<1300xf32>) -> tensor<1300xf32>
    %3 = linalg.matvec ins(%arg1, %arg2 : tensor<1300x1300xf32>, tensor<1300xf32>) outs(%1 : tensor<1300xf32>) -> tensor<1300xf32>
    %4 = linalg.generic {indexing_maps = [#map, #map1, #map1], iterator_types = ["parallel"]} ins(%cst, %2 : tensor<f32>, tensor<1300xf32>) outs(%0 : tensor<1300xf32>) {
    ^bb0(%in: f32, %in_2: f32, %out: f32):
      %7 = arith.mulf %in, %in_2 : f32
      linalg.yield %7 : f32
    } -> tensor<1300xf32>
    %5 = linalg.generic {indexing_maps = [#map, #map1, #map1], iterator_types = ["parallel"]} ins(%cst_1, %3 : tensor<f32>, tensor<1300xf32>) outs(%0 : tensor<1300xf32>) {
    ^bb0(%in: f32, %in_2: f32, %out: f32):
      %7 = arith.mulf %in, %in_2 : f32
      linalg.yield %7 : f32
    } -> tensor<1300xf32>
    %6 = linalg.generic {indexing_maps = [#map1, #map1, #map1], iterator_types = ["parallel"]} ins(%4, %5 : tensor<1300xf32>, tensor<1300xf32>) outs(%0 : tensor<1300xf32>) {
    ^bb0(%in: f32, %in_2: f32, %out: f32):
      %7 = arith.addf %in, %in_2 : f32
      linalg.yield %7 : f32
    } -> tensor<1300xf32>
    return %6 : tensor<1300xf32>
  }
}
