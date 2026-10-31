---
name: lassi-x-fp16-compensate
description: Reduce diagnosed FP16 or BF16 scientific error with hardware-aware accumulation, stable reformulation, state residuals, scaling, refinement, adaptive precision, multiword arithmetic, or stochastic casts. Use only after a base translation passes the original C/C++ FP64 oracle and a measured low-precision point is inaccurate or Pareto-dominated.
license: MIT
metadata:
  hermes:
    tags: [FP16, BF16, Mixed-Precision, Numerical-Methods, Pareto]
    requires_toolsets: [skills]
---
# Compensate FP16/BF16 Error

## Role

Act as a low-precision numerical methods specialist. Diagnose the error mechanism from
measurements and backend capabilities, then make one auditable source-level intervention whose
precision behavior is reported honestly.

Use the supplied diagnosis or load `lassi-x-fp-error-diagnose` to establish one, then read
[references/techniques.md](references/techniques.md) before editing.

For concrete PyTorch implementations, inspect
[`scripts/torch_cpu_techniques.py`](scripts/torch_cpu_techniques.py). It contains one runnable
template for every advertised technique and a CPU smoke test. Adapt a template to the assigned
kernel; do not copy a demonstration's assumptions blindly.

## Entry conditions

- The base module already matches the original C/C++ FP64 oracle.
- The target backend and FP16/BF16 measurement are explicitly identified.
- The target is a copy; never modify the accepted base candidate.

Establish missing prerequisites within the assigned tools, paths, and finite budget: create the
assigned target copy if needed, or run an authorized validation or baseline measurement. If the
FP64 gate, backend, measurement, or writable target remains unavailable, report the missing
evidence and stop before compensation edits. Never overwrite the accepted base.

## Workflow

1. Use the diagnosis skill to localize range loss, swamping, cancellation, conditioning,
   unstable function evaluation, iterative instability, or long-term rounding drift.
2. Run `lassi-x precision methods` and filter the allowed methods against actual backend
   capabilities. Never infer explicit FP32 tensor operations from a wider matrix accumulator.
3. Check the selected technique on the actual backend and dtype with a small relevant probe
   when operator availability is uncertain. The optional
   `python scripts/torch_cpu_techniques.py --smoke` checks all CPU examples; it is not an entry
   gate and does not establish suitability or improvement for the assigned kernel.
4. Before replacing an elementary function with an approximation, load
   `lassi-x-elementary-function-audit`. Choose one primary technique with a causal link to the diagnosed failure. Prefer the
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

## Diagnostics

Follow the [diagnostic output policy](../references/diagnostics.md).
Report precision roles, validation status, aggregate errors, latency statistics, and stochastic-trial distributions.

## Selection guidance

- Obey the experiment's arithmetic contract before considering backend capabilities. A GPU
  used to evaluate portability to a target-format-only accelerator does not authorize FP32.
- Under `target_format_only`, keep operators, persistent state, compensation/residuals and
  outputs in the target format. Do not use wider tensor casts or helpers that promote internally.
  Prefer scaling, stable reformulation, centering, reduction restructuring and target-format
  multiword arithmetic. Implicit wider hardware accumulation requires explicit target permission.
- Under an explicitly mixed-precision contract, consider selective FP32 accumulation. Promoting
  the entire computation is a fallback baseline, not a repair, even if output is cast back.
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
- Never regenerate known fixture values inside forward or move kernel work into build_inputs.
- Prefer one dtype-generic intervention and independently measure FP16 and BF16; success in one
  does not establish success in the other. FP16 range failures and BF16 significance failures
  can require different follow-up changes.
