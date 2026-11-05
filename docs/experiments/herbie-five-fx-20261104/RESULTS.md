# Five-model FX retry results

All five frozen sources were retried once, with no source changes or exclusions.
Four traced successfully. Three expose FX Herbie regions. These are syntactic
roots, potentially overlapping, with provisional tensor boundary contracts;
they are not validated repairs or counts of independent repair opportunities.

| Model | FX capture | FX regions | Static regions | Matmul precision proposals |
|---|---|---:|---:|---:|
| ATAX | Pass | 0 | 0 | 2 |
| GESUMMV | Pass | 3 | 1 | 2 |
| Covariance | Pass | 4 | 1 | 0 |
| Correlation | Pass | 8 | 1 | 1 |
| Deriche | Fail: symbolic control flow | 0 | 15 | 0 |

The declared FX extraction gate passed for 3/5 models. ATAX and Deriche failed
that capability gate, with zero infrastructure/incomplete attempts. Counting the
static fallback, 4/5 models expose expressions, as before, but FX now gives larger
cross-assignment expressions and additional roots. ATAX additionally has two
FP32 matmul proposals; these do not pass the Herbie extraction gate. Covariance's
method-form matmul is outside the current promotion helper's supported spelling.
Deriche raised `TraceError: symbolically traced variables cannot be used as inputs
to control flow`. No specialization or candidate edits were attempted.

No Herbie searches, numerical model evaluations, model calls, accelerator jobs,
C-reference comparisons, precision audits, latency tests or holdouts ran. Symbolic
forward tracing did execute Python. Runtime guards may reject regions whose
boundaries are Python scalars or have incompatible precision. Region domains have
not been established. Numerical improvement and repaired-model counts are zero.

Evidence: `runs/herbie-five-fx-20261104/summary.json` records all source hashes and
explicit evidence paths. Each `campaign/tasks/<kernel>/000001/work/evidence.json`
contains extracted wrappers, captured graphs, failure reasons and precision
proposal graphs. `environment.json` records versions and frozen implementation
hashes; campaign preparation snapshots all declared inputs. The prior experiments
remain untouched. Campaign run exit 1 reflects the two expected failed gates.

No retries remain or remote work is active. The next numerical experiment needs
explicit intermediate input domains and a reference/workload contract, then bounded
Herbie searches and full-model validation. This trial does not establish that the
new regions improve accuracy. Repository check results are in
`runs/herbie-five-fx-20261104/quality.log`.

Final locked development checks: lint, formatting, strict typing and tests all
passed; 602 tests passed, 3 skipped. No changes were pushed and no remote CI or
hardware result is claimed.
