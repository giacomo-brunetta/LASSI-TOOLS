# Five-model FX retry

Question: can the new deterministic FX adapter capture the same five unchanged
models and expose binary16 Herbie expressions? Unit: one frozen candidate/kernel.
Cohort: ATAX, GESUMMV, covariance, correlation, Deriche from the original explicit
`runs/herbie-five-torch-20261104/inputs/` snapshots and their specification hashes.
All five remain in the denominator. No candidate selection or source changes.

Protocol: `runs/herbie-five-fx-20261104/plan.yaml`; file identities, versions and
commit in `environment.json`, dirty patch in `working-tree.patch` in that directory.
Frozen campaign runner, sequential, one attempt per model, 30 seconds each,
150 seconds maximum task budget, zero retries, model calls or accelerators.
Symbolic tracing executes Python with proxy values. No builders or numerical
forward workloads run. No C oracle, input domain, numerical acceptance, latency,
precision certificate or holdout claim is attempted. No Herbie search is launched
without explicit intermediate domains. Sources and all three adapters are verified.

Gates: frozen inputs match; FX produces at least one Herbie region. Record static
fallback regions and matmul proposals independently; neither makes the FX gate
pass. Tracing failure or zero FX regions is unsupported; missing verdict/timeouts
are incomplete. Preserve all original campaign evidence. Capture all exceptions.

Launch: `uv run --locked lassi-x campaign prepare
runs/herbie-five-fx-20261104/plan.yaml runs/herbie-five-fx-20261104/campaign`, then
`uv run --locked lassi-x campaign run runs/herbie-five-fx-20261104/campaign`.
Local CPU only; no remote owners, credentials, model endpoints or jobs.
Results will be recorded in RESULTS.md with evidence paths. Next unresolved gate
is explicitly bounded Herbie search with justified region domains, then full-model
reference validation. No numerical repair is accepted by this capability trial.
