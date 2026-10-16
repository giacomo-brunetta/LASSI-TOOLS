# Strict precision rerun — 16 October 2026

Confirmed explicit arithmetic promotions from Terra, Luna and GPT-OSS were
invalidated only for their affected source/precision cells. Valid sibling
measurements and CPU FP64 translation evidence remain usable. The invalidation
manifest and recoverable candidate copies are under
`runs/legacy/precision-policy-20261016/confirmed-promotions/`.

The replacement campaign covers Deriche, Correlation, ADI, direct DFT and Durbin.
Each model generates its own translations at medium effort, with three candidates
per kernel. Terra's already-running fresh Deriche translation was reused rather
than generated twice. Models run serially: Terra, Luna, then GPT-OSS 120B via
OpenRouter pinned to Groq.

All 15 CPU kernel/model cases finished:

| Model | CPU FP64 verified kernels | Failed kernels |
| --- | --- | --- |
| Terra | 5/5 | None |
| Luna | 4/5 | Deriche |
| GPT-OSS 120B | 3/5 | Deriche, Durbin |

These are kernel-level CPU translation outcomes, not low-precision success rates.
At least one accepted candidate is required to count a kernel as verified.
Earlier Deriche failures were correctness/runtime failures, not quota errors.

The queue stopped at GPU preflight because Globus reported `ENDPOINT_NOT_ONLINE`
for endpoint `b162a840-38b4-4c1a-84cc-579fb62f4dfc`. No GPU compatibility or LARGE
evaluation stages ran. Numerical repair was disabled in this rerun. CPU outputs
are retained locally under `runs/three-model-strict-rerun-20261016/`, with reused
Terra Deriche output under `runs/terra-deriche-strict-rerun-20261016/`.
