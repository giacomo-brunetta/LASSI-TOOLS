#map = affine_map<(d0, d1) -> ()>
#map1 = affine_map<(d0, d1) -> (d0, d1)>
module attributes {torch.debug_module_name = "GemmMatmul"} {
  ml_program.global private mutable @global_seed(dense<0> : tensor<i64>) : tensor<i64>
  func.func @forward(%arg0: tensor<1000x1100xf32>, %arg1: tensor<1000x1200xf32>, %arg2: tensor<1200x1100xf32>) -> tensor<1000x1100xf32> {
    %cst = arith.constant dense<1.200000e+00> : tensor<f32>
    %cst_0 = arith.constant 0.000000e+00 : f32
    %cst_1 = arith.constant dense<1.500000e+00> : tensor<f32>
    %0 = tensor.empty() : tensor<1000x1100xf32>
    %1 = linalg.generic {indexing_maps = [#map, #map1, #map1], iterator_types = ["parallel", "parallel"]} ins(%cst, %arg0 : tensor<f32>, tensor<1000x1100xf32>) outs(%0 : tensor<1000x1100xf32>) {
    ^bb0(%in: f32, %in_2: f32, %out: f32):
      %6 = arith.mulf %in, %in_2 : f32
      linalg.yield %6 : f32
    } -> tensor<1000x1100xf32>
    %2 = linalg.fill ins(%cst_0 : f32) outs(%0 : tensor<1000x1100xf32>) -> tensor<1000x1100xf32>
    %3 = linalg.matmul ins(%arg1, %arg2 : tensor<1000x1200xf32>, tensor<1200x1100xf32>) outs(%2 : tensor<1000x1100xf32>) -> tensor<1000x1100xf32>
    %4 = linalg.generic {indexing_maps = [#map, #map1, #map1], iterator_types = ["parallel", "parallel"]} ins(%cst_1, %3 : tensor<f32>, tensor<1000x1100xf32>) outs(%0 : tensor<1000x1100xf32>) {
    ^bb0(%in: f32, %in_2: f32, %out: f32):
      %6 = arith.mulf %in, %in_2 : f32
      linalg.yield %6 : f32
    } -> tensor<1000x1100xf32>
    %5 = linalg.generic {indexing_maps = [#map1, #map1, #map1], iterator_types = ["parallel", "parallel"]} ins(%1, %4 : tensor<1000x1100xf32>, tensor<1000x1100xf32>) outs(%0 : tensor<1000x1100xf32>) {
    ^bb0(%in: f32, %in_2: f32, %out: f32):
      %6 = arith.addf %in, %in_2 : f32
      linalg.yield %6 : f32
    } -> tensor<1000x1100xf32>
    return %5 : tensor<1000x1100xf32>
  }
}
