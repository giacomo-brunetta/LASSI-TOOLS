---
name: compile-source
description: Compiles one or more C/C++/CUDA source files using a specific compiler (gcc, nvcc, etc.)
---

# Compile Source Instructions

Use this skill when you need to compile source code into an executable or object file.

1.  Identify the source files that need to be compiled.
2.  Select the appropriate compiler for the language (e.g., `gcc` for C, `g++` for C++, `nvcc` for CUDA).
3.  Specify any necessary compiler flags (e.g., `-O3`, `-Wall`).
4.  Provide paths to include directories and library directories if required.
5.  Optionally specify the output binary name.

## Code Template

```bash
python3 LASSI-TOOLS/skills/compile-source/compile_source.py \
    --path main.cpp utils.cpp \
    --compiler g++ \
    --kwds "-O3 -Wall" \
    --output my_app
```

## Common Issues

- **File Not Found**: Ensure the paths to source files are correct.
- **Compiler Missing**: Ensure the requested compiler is installed on the system.
- **Linker Errors**: Check if all required libraries and their paths are correctly specified.
