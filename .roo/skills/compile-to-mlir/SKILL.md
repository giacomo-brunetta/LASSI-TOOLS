---
name: compile-to-mlir
description: Compiles C/C++ source file(s) specifically to MLIR using cgeist
---

# Compile to MLIR Instructions

Use this skill when you need to transform C or C++ code into MLIR format using the `cgeist` tool.

1.  Identify the source files.
2.  Provide any specific `cgeist` flags (e.g., `-function=*`).
3.  Include necessary directory paths if the code depends on external headers or libraries.
4.  Specify the desired output filename for the MLIR file.

## Code Template

```bash
python3 LASSI-TOOLS/skills/compile-to-mlir/compile_to_mlir.py \
    --path input.cpp \
    --kwds "-function=*" \
    --output input.mlir
```

## Common Issues

- **cgeist Not Found**: Ensure `cgeist` is available in the environment.
- **Syntax Errors**: `cgeist` may be stricter or different from standard compilers; ensure the source code is compatible.
