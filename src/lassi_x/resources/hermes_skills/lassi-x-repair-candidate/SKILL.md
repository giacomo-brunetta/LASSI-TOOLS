---
name: lassi-x-repair-candidate
description: Repair a translated candidate from structured compile, runtime, shape, or C-reference mismatch diagnostics.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [file, terminal]
metadata:
  hermes:
    tags: [LASSI-X, Debugging, Numerical-Verification]
---
# Repair a Candidate

## Procedure
1. Treat the validator diagnostic as evidence, not as a request to loosen tolerances.
2. For compile/import failures, make the smallest structural repair and byte-compile.
3. For shape failures, trace reference live-outs and canonical flattening order.
4. For numerical failures, inspect the first mismatches, initialization, loop bounds,
   update ordering, dtype conversions, boundary conditions, and reductions.
5. Rerun `lassi-x validate candidate`; all gates restart after every repair.

## Prohibited repairs
- Embedding oracle values or reading the oracle output from the candidate.
- Changing tolerances, bypassing the runner, or returning a constant.
- Adding compensation to hide an FP64 semantic error.

## Verification
Success requires FP64 output to match the original C/C++ FP64 oracle.
