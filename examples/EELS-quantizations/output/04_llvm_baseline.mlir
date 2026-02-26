module attributes {soda.bambu.container_module, soda.container_module, tf.versions = {bad_consumers = [], min_consumer = 0 : i32, producer = 1882 : i32}} {
  llvm.func @forward_kernel(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr) {
    %0 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %1 = llvm.insertvalue %arg2, %0[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %2 = llvm.insertvalue %arg2, %1[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %3 = llvm.mlir.constant(0 : index) : i64
    %4 = llvm.insertvalue %3, %2[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %5 = llvm.mlir.constant(1 : index) : i64
    %6 = llvm.insertvalue %5, %4[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %7 = llvm.mlir.constant(16 : index) : i64
    %8 = llvm.insertvalue %7, %6[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %9 = llvm.mlir.constant(1 : index) : i64
    %10 = llvm.insertvalue %9, %8[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %11 = llvm.mlir.constant(16 : index) : i64
    %12 = llvm.insertvalue %11, %10[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %13 = llvm.mlir.constant(16 : index) : i64
    %14 = llvm.insertvalue %13, %12[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %15 = llvm.mlir.constant(1 : index) : i64
    %16 = llvm.insertvalue %15, %14[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %17 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %18 = llvm.insertvalue %arg1, %17[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %19 = llvm.insertvalue %arg1, %18[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %20 = llvm.mlir.constant(0 : index) : i64
    %21 = llvm.insertvalue %20, %19[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %22 = llvm.mlir.constant(1 : index) : i64
    %23 = llvm.insertvalue %22, %21[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %24 = llvm.mlir.constant(15360 : index) : i64
    %25 = llvm.insertvalue %24, %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %26 = llvm.mlir.constant(960 : index) : i64
    %27 = llvm.insertvalue %26, %25[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %28 = llvm.mlir.constant(16 : index) : i64
    %29 = llvm.insertvalue %28, %27[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %30 = llvm.mlir.constant(16 : index) : i64
    %31 = llvm.insertvalue %30, %29[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %32 = llvm.mlir.constant(1 : index) : i64
    %33 = llvm.insertvalue %32, %31[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %34 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %35 = llvm.insertvalue %arg0, %34[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %36 = llvm.insertvalue %arg0, %35[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %37 = llvm.mlir.constant(0 : index) : i64
    %38 = llvm.insertvalue %37, %36[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %39 = llvm.mlir.constant(1 : index) : i64
    %40 = llvm.insertvalue %39, %38[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %41 = llvm.mlir.constant(960 : index) : i64
    %42 = llvm.insertvalue %41, %40[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %43 = llvm.mlir.constant(1 : index) : i64
    %44 = llvm.insertvalue %43, %42[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %45 = llvm.mlir.constant(960 : index) : i64
    %46 = llvm.insertvalue %45, %44[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %47 = llvm.mlir.constant(960 : index) : i64
    %48 = llvm.insertvalue %47, %46[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %49 = llvm.mlir.constant(1 : index) : i64
    %50 = llvm.insertvalue %49, %48[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %51 = llvm.mlir.constant(960 : index) : i64
    %52 = llvm.mlir.constant(16 : index) : i64
    %53 = llvm.mlir.constant(1 : index) : i64
    %54 = llvm.mlir.constant(0 : index) : i64
    llvm.br ^bb1(%54 : i64)
  ^bb1(%55: i64):  // 2 preds: ^bb0, ^bb4
    %56 = llvm.icmp "slt" %55, %52 : i64
    llvm.cond_br %56, ^bb2(%54 : i64), ^bb5
  ^bb2(%57: i64):  // 2 preds: ^bb1, ^bb3
    %58 = llvm.icmp "slt" %57, %51 : i64
    llvm.cond_br %58, ^bb3, ^bb4
  ^bb3:  // pred: ^bb2
    %59 = llvm.extractvalue %50[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %60 = llvm.mlir.constant(960 : index) : i64
    %61 = llvm.mul %54, %60 : i64
    %62 = llvm.mlir.constant(960 : index) : i64
    %63 = llvm.mul %54, %62 : i64
    %64 = llvm.add %61, %63 : i64
    %65 = llvm.add %64, %57 : i64
    %66 = llvm.getelementptr %59[%65] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %67 = llvm.load %66 : !llvm.ptr -> f32
    %68 = llvm.extractvalue %33[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %69 = llvm.mlir.constant(15360 : index) : i64
    %70 = llvm.mul %54, %69 : i64
    %71 = llvm.mlir.constant(16 : index) : i64
    %72 = llvm.mul %57, %71 : i64
    %73 = llvm.add %70, %72 : i64
    %74 = llvm.add %73, %55 : i64
    %75 = llvm.getelementptr %68[%74] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %76 = llvm.load %75 : !llvm.ptr -> f32
    %77 = llvm.extractvalue %16[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %78 = llvm.mlir.constant(16 : index) : i64
    %79 = llvm.mul %54, %78 : i64
    %80 = llvm.mlir.constant(16 : index) : i64
    %81 = llvm.mul %54, %80 : i64
    %82 = llvm.add %79, %81 : i64
    %83 = llvm.add %82, %55 : i64
    %84 = llvm.getelementptr %77[%83] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %85 = llvm.load %84 : !llvm.ptr -> f32
    %86 = llvm.fmul %67, %76  : f32
    %87 = llvm.fadd %85, %86  : f32
    %88 = llvm.extractvalue %16[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %89 = llvm.mlir.constant(16 : index) : i64
    %90 = llvm.mul %54, %89 : i64
    %91 = llvm.mlir.constant(16 : index) : i64
    %92 = llvm.mul %54, %91 : i64
    %93 = llvm.add %90, %92 : i64
    %94 = llvm.add %93, %55 : i64
    %95 = llvm.getelementptr %88[%94] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %87, %95 : f32, !llvm.ptr
    %96 = llvm.add %57, %53 : i64
    llvm.br ^bb2(%96 : i64)
  ^bb4:  // pred: ^bb2
    %97 = llvm.add %55, %53 : i64
    llvm.br ^bb1(%97 : i64)
  ^bb5:  // pred: ^bb1
    llvm.return
  }
}

