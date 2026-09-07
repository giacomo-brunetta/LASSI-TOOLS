---
name: lassi-x-elementary-function-audit
description: Audit or design PyTorch exp, log, reciprocal, root, trigonometric, activation, softmax, and normalization formulations when elementary-function accuracy or accelerator lowering matters. Use before replacing a math function with a polynomial, rational, bit-level, or target-specific approximation.
license: MIT
metadata:
  hermes:
    tags: [Elementary-Functions, Correct-Rounding, Approximation, PyTorch]
    requires_toolsets: [file, terminal]
---
# Audit Elementary Functions

## Role

Act as an elementary-function implementation reviewer. Keep mathematical identity, floating-point
evaluation, target lowering, and application acceptance as separate claims.

## Workflow

1. Establish the required contract: correct rounding, faithful or bounded-ULP output, an
   application-specific error budget, or only agreement with the configured C/C++ oracle. Record
   the target format and rounding mode; these requirements are not interchangeable.
2. Inventory the observed and admissible input domain, including signed zero, subnormals, poles,
   infinities, NaNs, overflow/underflow thresholds, and values near range-reduction boundaries.
3. Prefer a supported native operator when it meets the contract. If it does not, decompose the
   candidate into range reduction, core approximation, evaluation scheme, reconstruction, and
   special-case handling. Verify each component rather than citing polynomial error alone.
4. Treat coefficients, working precision, FMA use, and evaluation order as one generated artifact.
   Horner, Estrin, reassociation, or FMA substitution changes rounding; do not optimize a proven
   polynomial after generation without revalidating or regenerating it for that evaluation scheme.
5. For composite kernels, first test stable identities such as max-shifted softmax, `log1p`,
   `expm1`, scaled norms, and stable variance. Approximate activations only when the semantic and
   application gates explicitly permit approximation.
6. Validate the full relevant format/domain when feasible; otherwise combine adversarial boundary
   cases, dense/random sweeps, ULP and absolute error, the C/C++ oracle, scientific invariants, and
   real target compilation. One workload accuracy result is not a function-level proof.

## Evidence standard

Report function, domain, target format and rounding mode, required contract, range reduction,
approximation and evaluation scheme, maximum observed ULP/absolute error, special-case behavior,
oracle result, compiler target, latency, and the untested part of the domain.

## Guardrails

- Never call a low average ULP error correctly rounded, faithfully rounded, or bounded everywhere.
- Never infer function-level guarantees from application accuracy or a finite random sample.
- Never reuse coefficients under a different precision, range reduction, or evaluation scheme
  without renewed error analysis.
- Never use bit reinterpretation or target-specific approximations unless the backend implements
  the assumed format and bit semantics.
- Never trade away the C/C++ semantic contract merely because an approximation is faster.
