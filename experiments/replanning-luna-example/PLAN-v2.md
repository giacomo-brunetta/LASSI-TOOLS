# Luna replanning development smoke test, version 2

This version inherits the one-kernel cohort, source hashes, model, resource,
session limits, artifact locations, and validation protocol in [PLAN.md](PLAN.md).
It is prepared after the version 1 baseline and before any Stage 2/3 model call.

Version 1 used relative L2 <= 0.01. All nine FP32/FP16/BF16 baseline cells passed,
so neither numerical planner would run. Their exact observations are preserved at
`runs/replanning-luna-correlation-mini-20261102/baseline-1pct.json`.

For this **feedback-informed development smoke test**, the numerical and target
accuracy gate is relative L2 <= 0.001, with finite outputs and input parity.
The already observed FP32 and FP16 cells meet this threshold; the BF16 cells do
not. Stage 2A may propose at most two same-precision repairs across all three
BF16 starting points. Stage 2B may propose at most two selective mixed-precision
repairs if the BF16 families remain invalid. Stage 3 may select any validated
FP32/FP16/BF16 realization and make at most two MPS specialization plans.

No result from this version is a final holdout or an unbiased estimate of repair
success at a preselected threshold. The original baseline is never rewritten.
