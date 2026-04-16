module attributes {torch.debug_module_name = "ThreeMMV4"} {
  func.func @forward(%arg0: tensor<800x1000xf32>, %arg1: tensor<1000x900xf32>, %arg2: tensor<900x1200xf32>, %arg3: tensor<1200x1100xf32>) -> tensor<?x?xf32> {
    %0 = "tosa.const"() <{value = dense<0.000000e+00> : tensor<?x?xf32>}> : () -> tensor<?x?xf32>
    %1 = tosa.reshape %arg0 {new_shape = array<i64: 1, 800, 1000>} : (tensor<800x1000xf32>) -> tensor<1x800x1000xf32>
    %2 = tosa.reshape %arg1 {new_shape = array<i64: 1, 1000, 900>} : (tensor<1000x900xf32>) -> tensor<1x1000x900xf32>
    %3 = tosa.matmul %1, %2 : (tensor<1x800x1000xf32>, tensor<1x1000x900xf32>) -> tensor<1x800x900xf32>
    %4 = tosa.reshape %3 {new_shape = array<i64: 800, 900>} : (tensor<1x800x900xf32>) -> tensor<800x900xf32>
    %5 = tosa.reshape %arg2 {new_shape = array<i64: 1, 900, 1200>} : (tensor<900x1200xf32>) -> tensor<1x900x1200xf32>
    %6 = tosa.reshape %arg3 {new_shape = array<i64: 1, 1200, 1100>} : (tensor<1200x1100xf32>) -> tensor<1x1200x1100xf32>
    %7 = tosa.matmul %5, %6 : (tensor<1x900x1200xf32>, tensor<1x1200x1100xf32>) -> tensor<1x900x1100xf32>
    %8 = tosa.reshape %7 {new_shape = array<i64: 900, 1100>} : (tensor<1x900x1100xf32>) -> tensor<900x1100xf32>
    %9 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 0>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %10 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 0, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %11 = tosa.reshape %9 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %12 = tosa.reshape %10 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %13 = tosa.matmul %11, %12 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %14 = tosa.reshape %13 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %15 = tosa.add %14, %0 : (tensor<800x1100xf32>, tensor<?x?xf32>) -> tensor<?x?xf32>
    %16 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 128>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %17 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 128, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %18 = tosa.reshape %16 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %19 = tosa.reshape %17 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %20 = tosa.matmul %18, %19 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %21 = tosa.reshape %20 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %22 = tosa.add %15, %21 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    %23 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 256>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %24 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 256, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %25 = tosa.reshape %23 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %26 = tosa.reshape %24 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %27 = tosa.matmul %25, %26 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %28 = tosa.reshape %27 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %29 = tosa.add %22, %28 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    %30 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 384>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %31 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 384, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %32 = tosa.reshape %30 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %33 = tosa.reshape %31 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %34 = tosa.matmul %32, %33 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %35 = tosa.reshape %34 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %36 = tosa.add %29, %35 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    %37 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 512>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %38 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 512, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %39 = tosa.reshape %37 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %40 = tosa.reshape %38 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %41 = tosa.matmul %39, %40 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %42 = tosa.reshape %41 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %43 = tosa.add %36, %42 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    %44 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 640>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %45 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 640, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %46 = tosa.reshape %44 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %47 = tosa.reshape %45 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %48 = tosa.matmul %46, %47 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %49 = tosa.reshape %48 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %50 = tosa.add %43, %49 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    %51 = tosa.slice %4 {size = array<i64: 800, 128>, start = array<i64: 0, 768>} : (tensor<800x900xf32>) -> tensor<800x128xf32>
    %52 = tosa.slice %8 {size = array<i64: 128, 1100>, start = array<i64: 768, 0>} : (tensor<900x1100xf32>) -> tensor<128x1100xf32>
    %53 = tosa.reshape %51 {new_shape = array<i64: 1, 800, 128>} : (tensor<800x128xf32>) -> tensor<1x800x128xf32>
    %54 = tosa.reshape %52 {new_shape = array<i64: 1, 128, 1100>} : (tensor<128x1100xf32>) -> tensor<1x128x1100xf32>
    %55 = tosa.matmul %53, %54 : (tensor<1x800x128xf32>, tensor<1x128x1100xf32>) -> tensor<1x800x1100xf32>
    %56 = tosa.reshape %55 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %57 = tosa.add %50, %56 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    %58 = tosa.slice %4 {size = array<i64: 800, 4>, start = array<i64: 0, 896>} : (tensor<800x900xf32>) -> tensor<800x?xf32>
    %59 = tosa.slice %8 {size = array<i64: 4, 1100>, start = array<i64: 896, 0>} : (tensor<900x1100xf32>) -> tensor<?x1100xf32>
    %60 = tosa.reshape %58 {new_shape = array<i64: 1, 800, -1>} : (tensor<800x?xf32>) -> tensor<1x800x?xf32>
    %61 = tosa.reshape %59 {new_shape = array<i64: 1, -1, 1100>} : (tensor<?x1100xf32>) -> tensor<1x?x1100xf32>
    %62 = tosa.matmul %60, %61 : (tensor<1x800x?xf32>, tensor<1x?x1100xf32>) -> tensor<1x800x1100xf32>
    %63 = tosa.reshape %62 {new_shape = array<i64: 800, 1100>} : (tensor<1x800x1100xf32>) -> tensor<800x1100xf32>
    %64 = tosa.add %57, %63 : (tensor<?x?xf32>, tensor<800x1100xf32>) -> tensor<?x?xf32>
    return %64 : tensor<?x?xf32>
  }
}
