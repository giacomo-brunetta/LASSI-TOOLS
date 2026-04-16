module attributes {torch.debug_module_name = "TwoMMV4"} {
  func.func @forward(%arg0: tensor<1xf32>, %arg1: tensor<1xf32>, %arg2: tensor<800x1100xf32>, %arg3: tensor<1100x900xf32>, %arg4: tensor<900x1200xf32>, %arg5: tensor<800x1200xf32>) -> tensor<800x1200xf32> {
    %0 = tosa.reshape %arg2 {new_shape = array<i64: 1, 800, 1100>} : (tensor<800x1100xf32>) -> tensor<1x800x1100xf32>
    %1 = tosa.reshape %arg3 {new_shape = array<i64: 1, 1100, 900>} : (tensor<1100x900xf32>) -> tensor<1x1100x900xf32>
    %2 = tosa.matmul %0, %1 : (tensor<1x800x1100xf32>, tensor<1x1100x900xf32>) -> tensor<1x800x900xf32>
    %3 = tosa.reshape %2 {new_shape = array<i64: 800, 900>} : (tensor<1x800x900xf32>) -> tensor<800x900xf32>
    %4 = tosa.reshape %arg0 {new_shape = array<i64: 1, 1>} : (tensor<1xf32>) -> tensor<1x1xf32>
    %5 = tosa.mul %4, %3 {shift = 0 : i8} : (tensor<1x1xf32>, tensor<800x900xf32>) -> tensor<800x900xf32>
    %6 = tosa.reshape %arg1 {new_shape = array<i64: 1, 1>} : (tensor<1xf32>) -> tensor<1x1xf32>
    %7 = tosa.mul %6, %arg5 {shift = 0 : i8} : (tensor<1x1xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %8 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 0>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %9 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 0, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %10 = tosa.reshape %8 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %11 = tosa.reshape %9 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %12 = tosa.matmul %10, %11 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %13 = tosa.reshape %12 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %14 = tosa.add %7, %13 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %15 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 128>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %16 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 128, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %17 = tosa.reshape %15 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %18 = tosa.reshape %16 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %19 = tosa.matmul %17, %18 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %20 = tosa.reshape %19 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %21 = tosa.add %14, %20 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %22 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 256>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %23 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 256, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %24 = tosa.reshape %22 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %25 = tosa.reshape %23 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %26 = tosa.matmul %24, %25 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %27 = tosa.reshape %26 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %28 = tosa.add %21, %27 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %29 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 384>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %30 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 384, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %31 = tosa.reshape %29 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %32 = tosa.reshape %30 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %33 = tosa.matmul %31, %32 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %34 = tosa.reshape %33 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %35 = tosa.add %28, %34 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %36 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 512>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %37 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 512, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %38 = tosa.reshape %36 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %39 = tosa.reshape %37 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %40 = tosa.matmul %38, %39 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %41 = tosa.reshape %40 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %42 = tosa.add %35, %41 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %43 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 640>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %44 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 640, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %45 = tosa.reshape %43 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %46 = tosa.reshape %44 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %47 = tosa.matmul %45, %46 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %48 = tosa.reshape %47 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %49 = tosa.add %42, %48 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %50 = tosa.slice %5 {size = array<i64: 800, 128>, start = array<i64: 0, 768>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %51 = tosa.slice %arg4 {size = array<i64: 128, 1200>, start = array<i64: 768, 0>} : (tensor<900x1200xf32>) -> tensor<128x1200xf32>
    %52 = tosa.reshape %50 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %53 = tosa.reshape %51 {new_shape = array<i64: 1, 128, 1200>} : (tensor<128x1200xf32>) -> tensor<1x128x1200xf32>
    %54 = tosa.matmul %52, %53 : (tensor<1x800x128xf32>, tensor<1x128x1200xf32>) -> tensor<1x800x1200xf32>
    %55 = tosa.reshape %54 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %56 = tosa.add %49, %55 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    %57 = tosa.slice %5 {size = array<i64: 800, 4>, start = array<i64: 0, 896>} : (tensor<800x900xf32>) -> tensor<800x?xf32>
    %58 = tosa.slice %arg4 {size = array<i64: 4, 1200>, start = array<i64: 896, 0>} : (tensor<900x1200xf32>) -> tensor<?x1200xf32>
    %59 = tosa.reshape %57 {new_shape = array<i64: 1, 800, -1>} : (tensor<800x?xf32>) -> tensor<1x800x?xf32>
    %60 = tosa.reshape %58 {new_shape = array<i64: 1, -1, 1200>} : (tensor<?x1200xf32>) -> tensor<1x?x1200xf32>
    %61 = tosa.matmul %59, %60 : (tensor<1x800x?xf32>, tensor<1x?x1200xf32>) -> tensor<1x800x1200xf32>
    %62 = tosa.reshape %61 {new_shape = array<i64: 800, 1200>} : (tensor<1x800x1200xf32>) -> tensor<800x1200xf32>
    %63 = tosa.add %56, %62 : (tensor<800x1200xf32>, tensor<800x1200xf32>) -> tensor<800x1200xf32>
    return %63 : tensor<800x1200xf32>
  }
}
