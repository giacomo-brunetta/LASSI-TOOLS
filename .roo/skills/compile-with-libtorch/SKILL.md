---
name: compile-with-libtorch
description: Compiles C++ source file(s) with LibTorch, automatically handling includes and library paths
---

# Compile with LibTorch Instructions

Use this skill when you need to compile C++ code that utilizes the LibTorch (PyTorch C++ API) library. It automatically locates the necessary headers and libraries.

1.  Identify the C++ source files.
2.  Provide any additional `g++` flags if needed.
3.  Specify extra include or library paths if your project has other dependencies.
4.  Specify the output binary name.

## Code Template

```bash
python3 ~/LASSI-TOOLS/.roo/skills/compile-with-libtorch/compile_with_libtorch.py \
    --path torch_app.cpp \
    --output torch_app
```

## Common Issues

- **LibTorch Not Found**: Ensure LibTorch is installed and the `CompilerTool.find_torchlib_paths()` logic can locate it.
- **ABI Mismatch**: This skill uses `-D_GLIBCXX_USE_CXX11_ABI=1` by default. If your LibTorch was built with a different ABI, you might need to adjust this.
