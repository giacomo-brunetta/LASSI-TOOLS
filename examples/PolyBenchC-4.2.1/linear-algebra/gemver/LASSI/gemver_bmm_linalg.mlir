#map = affine_map<(d0, d1) -> (d0, d1)>
#map1 = affine_map<(d0, d1) -> (d1, d0)>
#map2 = affine_map<(d0) -> ()>
#map3 = affine_map<(d0) -> (d0)>
module attributes {torch.debug_module_name = "GemverBmm"} {
  ml_program.global private mutable @global_seed(dense<0> : tensor<i64>) : tensor<i64>
  func.func @forward(%arg0: tensor<2000x2000xf32>, %arg1: tensor<2000xf32>, %arg2: tensor<2000xf32>, %arg3: tensor<2000xf32>, %arg4: tensor<2000xf32>, %arg5: tensor<2000xf32>, %arg6: tensor<2000xf32>, %arg7: tensor<2000xf32>, %arg8: tensor<2000xf32>) -> tensor<2000xf32> {
    %cst = arith.constant dense<1.200000e+00> : tensor<f32>
    %cst_0 = arith.constant 0.000000e+00 : f32
    %cst_1 = arith.constant dense<1.500000e+00> : tensor<f32>
    %expanded = tensor.expand_shape %arg1 [[0, 1, 2]] output_shape [1, 2000, 1] : tensor<2000xf32> into tensor<1x2000x1xf32>
    %expanded_2 = tensor.expand_shape %arg2 [[0, 1, 2]] output_shape [1, 1, 2000] : tensor<2000xf32> into tensor<1x1x2000xf32>
    %0 = tensor.empty() : tensor<1x2000x2000xf32>
    %1 = linalg.fill ins(%cst_0 : f32) outs(%0 : tensor<1x2000x2000xf32>) -> tensor<1x2000x2000xf32>
    %2 = linalg.batch_matmul ins(%expanded, %expanded_2 : tensor<1x2000x1xf32>, tensor<1x1x2000xf32>) outs(%1 : tensor<1x2000x2000xf32>) -> tensor<1x2000x2000xf32>
    %collapsed = tensor.collapse_shape %2 [[0, 1], [2]] : tensor<1x2000x2000xf32> into tensor<2000x2000xf32>
    %expanded_3 = tensor.expand_shape %arg3 [[0, 1, 2]] output_shape [1, 2000, 1] : tensor<2000xf32> into tensor<1x2000x1xf32>
    %expanded_4 = tensor.expand_shape %arg4 [[0, 1, 2]] output_shape [1, 1, 2000] : tensor<2000xf32> into tensor<1x1x2000xf32>
    %3 = linalg.batch_matmul ins(%expanded_3, %expanded_4 : tensor<1x2000x1xf32>, tensor<1x1x2000xf32>) outs(%1 : tensor<1x2000x2000xf32>) -> tensor<1x2000x2000xf32>
    %collapsed_5 = tensor.collapse_shape %3 [[0, 1], [2]] : tensor<1x2000x2000xf32> into tensor<2000x2000xf32>
    %4 = tensor.empty() : tensor<2000x2000xf32>
    %5 = linalg.generic {indexing_maps = [#map, #map, #map], iterator_types = ["parallel", "parallel"]} ins(%arg0, %collapsed : tensor<2000x2000xf32>, tensor<2000x2000xf32>) outs(%4 : tensor<2000x2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.addf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000x2000xf32>
    %6 = linalg.generic {indexing_maps = [#map, #map, #map], iterator_types = ["parallel", "parallel"]} ins(%5, %collapsed_5 : tensor<2000x2000xf32>, tensor<2000x2000xf32>) outs(%4 : tensor<2000x2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.addf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000x2000xf32>
    %7 = linalg.generic {indexing_maps = [#map, #map1], iterator_types = ["parallel", "parallel"]} ins(%6 : tensor<2000x2000xf32>) outs(%4 : tensor<2000x2000xf32>) {
    ^bb0(%in: f32, %out: f32):
      linalg.yield %in : f32
    } -> tensor<2000x2000xf32>
    %8 = tensor.empty() : tensor<2000xf32>
    %9 = linalg.fill ins(%cst_0 : f32) outs(%8 : tensor<2000xf32>) -> tensor<2000xf32>
    %10 = linalg.matvec ins(%7, %arg7 : tensor<2000x2000xf32>, tensor<2000xf32>) outs(%9 : tensor<2000xf32>) -> tensor<2000xf32>
    %11 = linalg.generic {indexing_maps = [#map2, #map3, #map3], iterator_types = ["parallel"]} ins(%cst, %10 : tensor<f32>, tensor<2000xf32>) outs(%8 : tensor<2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.mulf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000xf32>
    %12 = linalg.generic {indexing_maps = [#map3, #map3, #map3], iterator_types = ["parallel"]} ins(%arg6, %11 : tensor<2000xf32>, tensor<2000xf32>) outs(%8 : tensor<2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.addf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000xf32>
    %13 = linalg.generic {indexing_maps = [#map3, #map3, #map3], iterator_types = ["parallel"]} ins(%12, %arg8 : tensor<2000xf32>, tensor<2000xf32>) outs(%8 : tensor<2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.addf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000xf32>
    %14 = linalg.matvec ins(%6, %13 : tensor<2000x2000xf32>, tensor<2000xf32>) outs(%9 : tensor<2000xf32>) -> tensor<2000xf32>
    %15 = linalg.generic {indexing_maps = [#map2, #map3, #map3], iterator_types = ["parallel"]} ins(%cst_1, %14 : tensor<f32>, tensor<2000xf32>) outs(%8 : tensor<2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.mulf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000xf32>
    %16 = linalg.generic {indexing_maps = [#map3, #map3, #map3], iterator_types = ["parallel"]} ins(%arg5, %15 : tensor<2000xf32>, tensor<2000xf32>) outs(%8 : tensor<2000xf32>) {
    ^bb0(%in: f32, %in_6: f32, %out: f32):
      %17 = arith.addf %in, %in_6 : f32
      linalg.yield %17 : f32
    } -> tensor<2000xf32>
    return %16 : tensor<2000xf32>
  }
}
