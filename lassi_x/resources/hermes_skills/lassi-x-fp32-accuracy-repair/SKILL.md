---
name: lassi-x-fp32-accuracy-repair
description: Repair a source that passes the C/C++ FP64 semantic gate but fails the same-workload FP32 accuracy gate. Diagnose FP32 instability or dtype-specific behavior before low-precision or mixed-precision rescue.
license: MIT
metadata:
  hermes:
    tags: [FP32, Numerical-Repair, Stability, Diagnostics]
    requires_toolsets: [skills]
---
# Repair FP32 Accuracy Before Low-Precision Rescue

## Entry gate

The source must pass the original C/C++ FP64 semantic and input-parity gates,
but fail its FP32 accuracy gate on the **same** workload. A failed FP64 gate is a
translation or input-semantics problem; use `lassi-x-repair-candidate` instead.
Do not route either failure into FP16/BF16 mixed-precision rescue.

## Diagnosis and repair

Compare FP64, FP32 and low-precision outputs at the same inputs. Find the first
operation where FP32 error grows, then distinguish unstable arithmetic from an
FP32-only code path, unsupported operator, input conversion, or wrong constant.
Use bounded ranges, finite counts, norms, reduction lengths, and selected
indices. Read `lassi-x-compare-outputs` when localization needs it.

Useful FP32-preserving examples:

```python
# Avoid cancellation when x is near zero.
y = torch.log1p(x)                 # instead of torch.log(1 + x)

# Keep an FP32 running state but change reduction order.
parts = x.float().reshape(blocks, width).sum(dim=1)
total = parts.sum().to(torch.float32)

# Shift a large baseline out of an update before accumulating small changes.
deviation = state.float() - baseline.float()
deviation = deviation + update.float()
state = baseline.float() + deviation
```

These snippets illustrate FP32 execution only. Do not copy unconditional `.float()` casts
into an FP64 validation path: preserve the input dtype there. Centering must retain the
deviation across updates to avoid losing it again at every reconstruction.

These snippets are hypotheses, not generic replacements. Preserve the C
semantics at FP64, the actual input contract, output ordering, and dataset.
Keep the repaired FP32 execution in FP32. If it requires FP64 tensor work,
record that as a separate FP64 fallback, not an FP32 repair.

After each edit, rerun FP64 and FP32 gates and independently evaluate FP16 and
BF16 from the repaired source. A repaired FP32 source is a new realization with
its own hash and lineage. Only its low-precision descendants with a passing
FP32 control may enter LP or MP planning. Preserve failed attempts and do not
select a source merely because another formulation happens to pass.

Follow the shared [diagnostic output policy](../references/diagnostics.md).
