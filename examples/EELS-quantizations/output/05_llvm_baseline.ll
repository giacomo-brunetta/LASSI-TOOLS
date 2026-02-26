; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define void @forward_kernel(ptr %0, ptr %1, ptr %2) {
  %4 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %2, 0
  %5 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %4, ptr %2, 1
  %6 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %5, i64 0, 2
  %7 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %6, i64 1, 3, 0
  %8 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %7, i64 16, 4, 0
  %9 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %8, i64 1, 3, 1
  %10 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %9, i64 16, 4, 1
  %11 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %10, i64 16, 3, 2
  %12 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %11, i64 1, 4, 2
  %13 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %1, 0
  %14 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %13, ptr %1, 1
  %15 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %14, i64 0, 2
  %16 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %15, i64 1, 3, 0
  %17 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %16, i64 15360, 4, 0
  %18 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %17, i64 960, 3, 1
  %19 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %18, i64 16, 4, 1
  %20 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %19, i64 16, 3, 2
  %21 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %20, i64 1, 4, 2
  %22 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %0, 0
  %23 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %22, ptr %0, 1
  %24 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %23, i64 0, 2
  %25 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %24, i64 1, 3, 0
  %26 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %25, i64 960, 4, 0
  %27 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %26, i64 1, 3, 1
  %28 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %27, i64 960, 4, 1
  %29 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %28, i64 960, 3, 2
  %30 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %29, i64 1, 4, 2
  br label %31

31:                                               ; preds = %58, %3
  %32 = phi i64 [ %59, %58 ], [ 0, %3 ]
  %33 = icmp slt i64 %32, 16
  br i1 %33, label %34, label %60

34:                                               ; preds = %37, %31
  %35 = phi i64 [ %57, %37 ], [ 0, %31 ]
  %36 = icmp slt i64 %35, 960
  br i1 %36, label %37, label %58

37:                                               ; preds = %34
  %38 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %30, 1
  %39 = add i64 0, %35
  %40 = getelementptr float, ptr %38, i64 %39
  %41 = load float, ptr %40, align 4
  %42 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %21, 1
  %43 = mul i64 %35, 16
  %44 = add i64 0, %43
  %45 = add i64 %44, %32
  %46 = getelementptr float, ptr %42, i64 %45
  %47 = load float, ptr %46, align 4
  %48 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %12, 1
  %49 = add i64 0, %32
  %50 = getelementptr float, ptr %48, i64 %49
  %51 = load float, ptr %50, align 4
  %52 = fmul float %41, %47
  %53 = fadd float %51, %52
  %54 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %12, 1
  %55 = add i64 0, %32
  %56 = getelementptr float, ptr %54, i64 %55
  store float %53, ptr %56, align 4
  %57 = add i64 %35, 1
  br label %34

58:                                               ; preds = %34
  %59 = add i64 %32, 1
  br label %31

60:                                               ; preds = %31
  ret void
}

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
