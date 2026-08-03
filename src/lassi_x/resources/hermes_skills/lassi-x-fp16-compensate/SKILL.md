---
name: lassi-x-fp16-compensate
description: Diagnose and compensate FP16/BF16 scientific error using hardware-aware reductions, state representations, scaling, refinement, or stochastic rounding.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [file, terminal]
metadata:
  hermes:
    tags: [LASSI-X, FP16, Mixed-Precision, Numerical-Methods, Pareto]
---
# FP16/BF16 Error Compensation

Compensation applies only after the base candidate matches the original C/C++ FP64 oracle.
Read [references/techniques.md](references/techniques.md) before editing.
Use `lassi-x precision methods` for the installed catalog and
`lassi-x precision measure --config CONFIG --module MODULE --backend NAME --precision fp16`
for a deterministic measurement against the configured C/C++ FP64 oracle.

## Procedure
1. Diagnose swamping, magnitude mismatch, overflow/underflow, iterative instability, or
   long-term rounding drift from measured evidence.
2. Filter methods by backend capabilities.
3. Apply one primary technique to a copy of the base module and declare precision roles.
4. Validate compensated FP64 against the original C/C++ FP64 oracle.
5. Validate compensated FP32 against the base PyTorch FP32 result.
6. Measure FP16/BF16 against the original C/C++ FP64 oracle and its scientific invariant.
7. For stochastic rounding, report multiple seeded runs.

## Rules
- Prefer FP32 accumulation on GPUs that expose it.
- Pairwise/Kahan rarely beat `torch.sum`; reserve them for manual reductions.
- Use FP16 double-word where explicit FP32 arithmetic is unavailable.
- Do not describe a point as FP16 without recording persistent-state and accumulator dtype.
