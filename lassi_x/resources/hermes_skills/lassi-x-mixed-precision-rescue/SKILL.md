---
name: lassi-x-mixed-precision-rescue
description: Repair a low-precision numerical failure by selectively promoting named operations or intermediates after FP64 semantics and the same-source FP32 control pass. Use only under an explicit mixed-precision contract and backend capability profile.
license: MIT
metadata:
  hermes:
    tags: [FP16, BF16, Mixed-Precision, Numerical-Repair]
    requires_toolsets: [skills]
---
# Selective Mixed-Precision Rescue

## Entry gate

Confirm that the selected source passes the C/C++ FP64 semantic gate and its
FP32 accuracy gate on the same workload and inputs. If FP32 is inaccurate, stop
and use `lassi-x-fp32-accuracy-repair` before attempting this skill. Confirm that
the target backend supports each proposed wider operation. A wider hardware
matrix accumulator does not imply support for arbitrary FP32 tensor operations.

Use `lassi-x-fp-error-diagnose` to localize the low-precision failure, then read
[references/upcasting.md](references/upcasting.md) for concrete PyTorch patterns.
This skill applies only when the experiment explicitly enables selective wider
arithmetic. The planner's chosen source and strategy are binding for the coder.

## Workflow

1. Identify the smallest tensor, reduction, or expression whose low-precision
   rounding plausibly causes the measured failure. State its input and output dtype.
2. Implement a local FP32 computation while keeping unrelated operators,
   persistent state, and low-precision storage in the requested format. Name all
   casts, wider intermediates, and wider operators in the plan and result.
3. Keep the C oracle, input contract, workload, tolerances, and output coverage
   unchanged. Recheck FP64 semantics and the same-source FP32 control.
4. Audit the executed or lowered graph. Record the operations actually promoted,
   including helpers and casts. Compare this inventory with the planned pattern;
   additional promotions require a revised plan and fresh validation.
5. Measure low-precision accuracy and latency on the target. Compare with the
   original low-precision candidate and the full FP32 baseline.

## Boundaries

- Casting the entire input to FP32 and running the whole forward in FP32 is
  `FP32_FALLBACK`, even if the output is cast down. Do not label it MP repair.
- A selective repair must retain a meaningful low-precision computation, such
  as a low-precision matrix multiply with FP32 reduction, or low-precision state
  with one FP32 residual calculation.
- Do not treat source-level dtype metadata or a passing numerical result as a
  precision certificate. If the backend cannot audit the pattern, report it as
  unverified.
- Do not replace the selected planner strategy, embed oracle values, relax
  tolerances, or use an unsupported operator to get a local pass.

Follow the shared [diagnostic output policy](../references/diagnostics.md).
