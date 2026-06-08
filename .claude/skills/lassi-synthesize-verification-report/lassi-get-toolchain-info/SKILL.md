---
name: lassi-get-toolchain-info
description: Report effective Python, torch, torch-mlir, and LLVM-related toolchain versions. Use when diagnosing version skew before a translation/export task or when the user asks "what version of torch-mlir do we have".
allowed-tools:
  - Bash(python cli/lassi-get-toolchain-info.py*)
  - Bash(python3 cli/lassi-get-toolchain-info.py*)
---

Returns versions for Python, torch, torch-mlir, llvm/mlir bins, and other components that participate in the C → torch → MLIR → SODA pipeline.

## Invocation

```
python cli/lassi-get-toolchain-info.py
```

No arguments.

## Underlying impl

`lassi.integrations.toolchain_info.get_toolchain_info_impl`
