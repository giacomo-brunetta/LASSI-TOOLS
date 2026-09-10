---
name: lassi-x-fp16-compensate
description: Reduce diagnosed FP16 or BF16 scientific error with hardware-aware accumulation, stable reformulation, state residuals, scaling, refinement, adaptive precision, multiword arithmetic, or stochastic casts. Use only after a base translation passes the original C/C++ FP64 oracle and a measured low-precision point is inaccurate or Pareto-dominated.
license: MIT
metadata:
  hermes:
    tags: [FP16, BF16, Mixed-Precision, Numerical-Methods, Pareto]
    requires_toolsets: [file, terminal]
---
# Compensate FP16/BF16 Error

## Role

Act as a low-precision numerical methods specialist. Diagnose the error mechanism from
measurements and backend capabilities, then make one auditable source-level intervention whose
precision behavior is reported honestly.

Load `lassi-x-fp-error-diagnose`, then read
[references/techniques.md](references/techniques.md) before editing.

For concrete PyTorch implementations, inspect
[`scripts/torch_cpu_techniques.py`](scripts/torch_cpu_techniques.py). It contains one runnable
template for every advertised technique and a CPU smoke test. Adapt a template to the assigned
kernel; do not copy a demonstration's assumptions blindly.

## Entry conditions

- The base module already matches the original C/C++ FP64 oracle.
- The target backend and FP16/BF16 measurement are explicitly identified.
- The target is a copy; never modify the accepted base candidate.

If any condition is missing, stop and report the missing evidence.

## Workflow

1. Use the diagnosis skill to localize range loss, swamping, cancellation, conditioning,
   unstable function evaluation, iterative instability, or long-term rounding drift.
2. Run `lassi-x precision methods` and filter the allowed methods against actual backend
   capabilities. Never infer explicit FP32 tensor operations from a wider matrix accumulator.
3. If the target is PyTorch CPU, run
   `python scripts/torch_cpu_techniques.py --smoke` from this skill directory before selecting a
   template. A passing demonstration establishes operator availability, not suitability or an
   accuracy improvement for the assigned kernel.
4. Choose one primary technique with a causal link to the diagnosed failure. Prefer the
   smallest change that tests the hypothesis cleanly.
5. Edit only the target copy. Reuse `lassi_x.precision` primitives where applicable and update
   `LASSI_PRECISION` storage, operator, accumulator, and output roles truthfully.
6. Byte-compile the target.
7. Validate compensated FP64 against the original C/C++ FP64 oracle.
8. Validate compensated FP32 against the base PyTorch FP32 behavior.
9. Measure the target precision against the C/C++ FP64 oracle:
   `lassi-x precision measure --config CONFIG --module MODULE --backend NAME --precision PRECISION`
10. Compare error reduction and latency cost. For stochastic rounding, report multiple seeds and
   distributional statistics rather than one favorable run.

## Selection guidance

- Prefer FP32 accumulation when the backend exposes it.
- Use blocked FP32 accumulation when full FP32 accumulation is costly and blockwise low-precision
  work is measurable. Tune the block size on the target.
- Reserve pairwise, Kahan, and Neumaier for manual reductions; low-precision compensation state
  can itself be lost, and optimized `torch.sum` may win.
- Use target-format double-word only when wider explicit arithmetic is unavailable and strict
  evaluation is preserved by the backend. Do not convert BF16 components to FP16.
- Use zero-centering or scaling only when the transformation is algebraically justified.
- Use refinement only when the problem structure supports a meaningful residual correction.
- Use stochastic casts only at explicit update/storage boundaries; they do not change the
  rounding of intervening arithmetic.

## Evidence standard

Report the diagnosed failure mode, selected technique, backend capability that permits it,
precision roles, FP64 result, FP32-collapse result, target-precision errors, invariant result,
latency, and comparison with the base point.

## Guardrails

- Never compensate an FP64 semantic error.
- Never read or embed oracle values, weaken gates, or relabel higher-precision storage as FP16.
- Never claim improvement without paired base and compensated measurements.
- Never hide compiler reassociation, fusion, or flush-to-zero risks.
- Never claim unbiased stochastic arithmetic from a software cast helper alone.
