# Explicit FP64 Deriche retry

Created `runs/herbie-deriche-fp64-20261104/deriche.py` from the frozen original.
Removed the conditional FP64-to-FP32 conversion and conditional output cast.
Inputs are unconditionally converted to FP64, and initializer floating values and
precision metadata now specify FP64. The original snapshot is untouched. The
variant intentionally ignores the builder dtype argument and returns FP64 inputs.
Source and parent hashes are in deriche.json alongside the candidate.

The one planned campaign capture attempt completed with a failed extraction gate.
A separately recorded diagnostic trace identified the new blocker at `_scan`:
`pad = -length % _PANEL_WIDTH; if pad:`. Shape is symbolic under ordinary FX, so
Python cannot decide the branch. The prior dtype branch no longer blocks capture.
The loop bound later also depends on shape. Fixed-shape capture/export is the
next approach; this run did not specialize or alter those control structures.
Full traceback: `runs/herbie-deriche-fp64-20261104/traceback.txt`.

One CPU development execution on fixed 4x4 FP64 inputs completed with a finite
16-element FP64 result. A TorchDispatchMode observer saw only torch.float64 for
floating operation outputs. This is observed execution evidence for this small
case, not a compiler precision audit or C-reference validation. Check script and
runtime-check.json are alongside the candidate. The large input builder was not
executed. No Herbie search, numerical repair acceptance, accelerator, timing or
holdout evaluation occurred.

Two symbolic traces total (campaign plus traceback diagnostic), one numerical
smoke invocation; no retries or active work remain. Framework source is unchanged;
prior full repository checks were 602 passed, 3 skipped. This candidate has its own
new runtime evidence and remains unvalidated against the original reference.

The archived precision metadata explicitly described its original downcast as
"FP64 C-float emulation". This gives evidence of the intended original policy,
but correctness of that emulation was not verified here. The new all-FP64 variant
changes that policy as requested.
