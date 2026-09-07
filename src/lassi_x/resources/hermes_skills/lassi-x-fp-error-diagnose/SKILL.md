---
name: lassi-x-fp-error-diagnose
description: Localize FP16 or BF16 error mechanisms in a validated PyTorch scientific kernel before choosing compensation. Use when a low-precision result is inaccurate, non-finite, unstable, or unexplained, or when a proposed intervention lacks causal evidence.
license: MIT
metadata:
  hermes:
    tags: [FP16, BF16, Diagnostics, Numerical-Analysis]
    requires_toolsets: [file, terminal]
---
# Diagnose Low-Precision Error

## Role

Act as a floating-point failure analyst. Produce a testable explanation of where accuracy is lost;
do not prescribe compensation from an aggregate error metric alone.

## Workflow

1. Confirm that the base module already passes the original C/C++ FP64 oracle. Otherwise classify
   the issue as translation error and stop the low-precision diagnosis.
2. Record the target backend, storage/operator/accumulator/output formats, rounding behavior,
   subnormal handling, and compiler reassociation or fusion risks. A wide matrix accumulator does
   not imply general FP32 tensor arithmetic.
3. Inspect the algorithm and dataflow for these mechanisms:
   - range loss: cast overflow, underflow, subnormal flushing, or poor use of the exponent range;
   - significance loss: swamping, long reductions, small recurrent updates, or mixed magnitudes;
   - cancellation or conditioning: a small result formed from large terms, ill-conditioned solves,
     or unstable recurrences;
   - function error: range reduction, approximation, special values, or unstable composites such
     as naive softmax, variance, `log(1+x)`, or `exp(x)-1`;
   - nondeterminism: reduction order or stochastic rounding variability.
4. When execution is available, use paired, one-variable probes: widen only the accumulator, alter
   only block size/order, apply an exact power-of-two scale, retain a discarded update residual, or
   repeat explicit stochastic casts across seeds. Measure the same dataset and oracle each time.
5. Use scale-aware evidence: value ranges, zero/subnormal/non-finite counts, cancellation ratios,
   reduction length, residual or invariant history, and all three aggregate error metrics. Treat a
   near-zero relative-error spike separately from a large absolute or normwise error.
6. State the earliest plausible error-amplifying operation, confidence, competing explanations,
   and the smallest intervention that would falsify the diagnosis. Then hand off to
   `lassi-x-fp16-compensate`.

## Evidence standard

Report the FP64 gate, backend precision contract, dataset, observed failure signature, localized
operation, paired probe results, conditioning or cancellation evidence, and unresolved uncertainty.
Distinguish measured backend behavior from source inspection and theoretical expectation.

## Guardrails

- Never diagnose from `max_rel_error` alone, especially when the reference is near zero.
- Never call a forward-error symptom proof of the underlying rounding mechanism.
- Never assume that a dtype name determines internal accumulation, subnormal, or rounding behavior.
- Never use oracle values as constants or weaken validation to make a hypothesis appear correct.
- Never recommend stochastic rounding from one seed or an elementary approximation from one input.
