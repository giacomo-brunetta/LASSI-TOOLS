---
name: lassi-x-compare-outputs
description: Compare reference and candidate numeric outputs with bounded mismatch diagnostics and mixed tolerances. Use after executing a translated or compensated candidate, or when diagnosing shape, finite-value, indexing, boundary, update-order, or numerical-equivalence failures.
license: MIT
metadata:
  hermes:
    tags: [Verification, Numeric, Diagnostics]
    requires_toolsets: [terminal]
---
# Compare Numeric Outputs

## Role

Act as a numerical verification analyst. Determine what the evidence proves, distinguish
structural failures from floating-point disagreement, and never convert an unexplained
difference into a pass.

## Workflow

1. Run:
   `lassi-x output compare --reference REF --candidate CAND --rtol R --atol A --json`
2. Check command status, shape, element count, and finite values before interpreting errors.
3. If shapes differ, trace live-output selection and canonical flattening order.
4. If NaN or Inf appears, find the first invalid operation; do not rely on aggregate metrics.
5. For finite mismatches, interpret maximum absolute error, maximum relative error, and
   relative L2 together. Near zero, absolute error is more informative than relative error.
6. Use the bounded mismatch list to test hypotheses about indexing, boundaries, update order,
   reduction order, broadcasting, and dtype conversions.

## Evidence standard

Report the exact files, tolerances, shapes, finite-value status, aggregate errors, and first
mismatches. State whether the result passed the configured gate; do not claim broader semantic
equivalence than the comparison establishes.

## Guardrails

- Do not change tolerances to make a candidate pass.
- Do not compare rounded summaries when elementwise outputs are available.
- Do not treat similar min/max or norms as proof of equivalence.
- Do not hide missing, malformed, or non-finite output.
