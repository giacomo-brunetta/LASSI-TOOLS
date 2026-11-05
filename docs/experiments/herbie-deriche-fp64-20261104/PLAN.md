# Explicit FP64 Deriche retry

User requested changing the archived Deriche to all FP64 and removing its dtype
branch. Preserve parent source; new source and parent hashes in
`runs/herbie-deriche-fp64-20261104/deriche.json`. Framework unchanged from previous
five-model FX trial, environment references and adapter hashes in environment.json.

One candidate, one CPU symbolic capture task, binary64 extraction, 30 seconds,
one attempt, zero retries, Herbie searches, model calls or accelerator jobs.
Frozen campaign at `runs/herbie-deriche-fp64-20261104/campaign`; plan.yaml alongside.
Gate: captured FX graph exposes at least one region. Unsupported capture is a
failed capability gate; missing verdict is incomplete. Retain all outcomes.

Additional development check: one CPU forward on a fixed 4x4 image containing
arange(16)/16 and scalar alpha=0.25, both FP64. Check finite FP64 output and inspect
executed floating-operation outputs for unintended lower precision. Budget 30s.
No builder runs the historical 4096x2160 workload. No oracle, error improvement,
performance, target or holdout claim. Changed precision requires fresh reference
validation before scientific acceptance. No active remote work or credentials.

Launch with lassi-x campaign prepare plan.yaml campaign, then campaign run campaign
using these explicit paths and the locked uv environment. Record results and
remaining blockers in RESULTS.md. No source correction after launch is budgeted.

Post-outcome diagnostic allowance: one additional symbolic trace, 30 seconds,
solely to save the full traceback of the unchanged failed candidate. It does not
replace the campaign verdict or permit a source correction.
