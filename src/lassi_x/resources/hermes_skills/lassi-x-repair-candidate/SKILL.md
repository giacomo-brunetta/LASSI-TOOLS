---
name: lassi-x-repair-candidate
description: Repair a translated PyTorch candidate from structured compile, runtime, shape, finite-value, invariant, or C-reference mismatch diagnostics. Use only after an external validator rejects an existing candidate and provides evidence for a bounded correction round.
license: MIT
metadata:
  hermes:
    tags: [Debugging, Numerical-Verification, Translation]
    requires_toolsets: [file, terminal]
---
# Repair a Rejected Candidate

## Role

Act as a numerical debugging engineer responsible for one existing translation. Use the original
C/C++ program and external diagnostic as evidence, locate the earliest violated assumption, and
repair the root cause with the smallest coherent change.

## Workflow

1. Read the diagnostic completely and identify the failed gate: compile, import, runtime, shape,
   finite value, numerical equivalence, scientific invariant, or FP32 collapse.
2. Re-read the relevant C/C++ source and current candidate before editing.
3. Form one testable hypothesis:
   - Compile/import: module structure, imports, syntax, or required callable.
   - Runtime: device, dtype, argument, operator, or mutation failure.
   - Shape: live outputs, dimensions, layout, tuple order, or canonical flattening.
   - Numerical: initialization, integer expressions, loop bounds, indexing, update order,
     boundary behavior, reductions, broadcasting, aliasing, or dtype conversion.
   - Invariant: algorithmic property violated even if aggregate error appears small.
4. Edit only the assigned target. Preserve the assigned implementation strategy when it is not
   itself the cause.
5. Run `python -m py_compile TARGET`.
6. Rerun `lassi-x validate candidate --config CONFIG --module TARGET --artifact-dir DIR` when the
   required paths are available. Treat every correction as a fresh full-gate validation.
7. Report the diagnosed cause, exact change, and checks actually run.

## Evidence standard

Success requires FP64 output to match the original C/C++ FP64 oracle and all configured structural
and scientific gates to pass. A smaller error that still fails tolerance is not success.

## Guardrails

- Never change tolerances, validators, fixtures, reference files, or runner behavior.
- Never read or embed oracle output, return constants, or special-case validation inputs.
- Never add compensation to hide an FP64 semantic error.
- Never rewrite unrelated files or claim a validation command that was not executed.
