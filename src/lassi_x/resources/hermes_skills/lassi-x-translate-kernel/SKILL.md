---
name: lassi-x-translate-kernel
description: Translate a C/C++ scientific kernel into the strict LASSI-X PyTorch candidate contract.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [file, terminal]
metadata:
  hermes:
    tags: [LASSI-X, PyTorch, Scientific-Computing, Translation]
---
# Translate a Scientific Kernel

## When to use
Use when an arena role is assigned one C/C++ to PyTorch strategy.

## Procedure
1. Read the reference source and every supplied header. Reproduce its dataset sizes,
   initialization, loop bounds, update order, and live output.
2. Write only the requested target module.
3. Define `build_inputs(device="cpu", dtype=torch.float64, fixture=None) -> tuple`.
4. Define `make_model() -> torch.nn.Module`; `forward(*inputs)` returns tensors in
   canonical reference order.
5. Define `LASSI_PRECISION` with `storage`, `operator`, `accumulator`, and `output`.
6. Keep FP64 semantics faithful to the C/C++ reference. Do not embed expected output.
7. Run `python -m py_compile <target>`.

## Pitfalls
- PyTorch broadcasting can silently change loop semantics.
- In-place updates versus double buffering must match the reference.
- Do not use low precision during input construction when the reference initializes in double.

## Verification
The authoritative gate is `lassi-x validate candidate --config CONFIG --module TARGET`.
