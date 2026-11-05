# Herbie adapter on five existing Torch models

**0/5 models supported by the current extraction adapter.** All five unchanged
archived sources were tried in the declared FP16 capability gate. None reached
FPCore generation, a native Herbie search, or numerical evaluation. This is an
adapter coverage result, not evidence that Herbie cannot improve their arithmetic.

| Model | Exact first rejection | Further structure visible in the unchanged source |
| --- | --- | --- |
| ATAX | `Unsupported Torch expression: torch.matmul(A, x)` | Two matrix-vector products, transpose and reshape |
| GESUMMV | `Unsupported Torch expression: torch.matmul(a, x)` | Matrix-vector products followed by elementwise combination |
| Covariance | `Require a stateless torch.nn.Module containing only forward` | Uses the `nn.Module` alias; also contains reduction, transpose/matmul and tuple output |
| Correlation | `Unsupported Torch expression: data.shape[0]` | Shape-derived dimension, reductions, conditional normalization and matrix product |
| Deriche | `Require a stateless torch.nn.Module containing only forward` | Additional helper methods, scans, shifts and dtype-dependent control flow |

Covariance's first diagnostic is an import/base-class spelling restriction,
not evidence that it contains persistent model state. Deriche is also rejected
by the whole-class contract before its arithmetic is examined. Neither source
was normalized, rewritten, replaced or reduced to a toy expression for this test.

## Cohort, attempts and evidence

The [plan](PLAN.md) declares five fixed kernel names and their historical
`c1-fp16.py` source slots from `a100-full-large-revalidation-20261017`. The missing
original run files were reconstructed byte-for-byte from the explicit archived
`source_index.json`; every source matches its historical SHA256. This was not a
selection of whichever sources passed the adapter. There is one source per
kernel and no alternative implementation search.

The complete local artifact root is
`/Users/giacomobrunetta/Projects/LASSI-TOOLS/runs/herbie-five-torch-20261104`:

- `cohort.json`, `inputs/`: every source identity, original path, class and snapshot.
- `environment.json`, `working-tree.patch`: harness, environment and input identities.
- `campaign.yaml`, `campaign/`: first frozen plan and five incomplete wrapper attempts.
- `recovery.yaml`, `recovery-identities.json`, `recovery-campaign/`: explicitly
  amended reporting recovery and five completed extraction outcomes.
- `recovery-campaign/tasks/<model>/000001/work/evidence.json`: exact rejection,
  source hash, static calls/methods and validation exclusions for each model.
- `summary.json`: complete counts and all five task/attempt/evidence identities.
- `quality.log`: repository development checks.

The first experiment wrapper incorrectly treated `StageContext.work_dir` as a
`Path` rather than a string. Its attempts reached extraction but could not write
reports, so their campaign outcomes remain incomplete. The corrected wrapper
only converts that path; the replacement campaign freezes the same source bytes
and Herbie adapter. Both histories are retained, and the plan amendment permits
exactly five replacement reporting attempts. No other retry or source adaptation
was performed. A campaign exit code of one is expected when its scientific
capability checks fail; the per-task records distinguish these failures from
the earlier infrastructure failures.

| Count | Outcome |
| --- | --- |
| Planned candidates / kernels / FP16 extraction cells | 5 / 5 / 5 |
| Completed capability attempts in replacement campaign | 5 |
| Supported models / kernels | 0 / 0 |
| Unsupported models / kernels | 5 / 5 |
| Initial incomplete reporting attempts | 5 |
| Total wrapper invocations, including recovery | 10 |
| Native Herbie searches | 0 |
| Torch forward executions | 0 |
| Model calls / accelerator jobs | 0 / 0 |
| Numerically qualified repairs | 0 |

No tensor input domain, C oracle, workload shape, input-parity gate, FP32 control,
executed precision audit, target measurement or independent holdout was evaluated.
There are no error reductions or speedups to report for this cohort. Historical
comments calling large dimensions "MINI" were not adopted as workload evidence.

## Implication for the next implementation

The useful next step is deterministic extraction and reinsertion of **elementwise
regions inside a larger Torch graph**, preserving matrix products, reductions,
indexing and output structure. GESUMMV's final elementwise combination is one
concrete candidate region, but its input ranges would need a trusted workload
contract before search. Import aliases and static shape expressions are smaller
frontend extensions; adding them alone would not handle covariance or correlation.

Reduction accumulation and recurrent state require separate treatment. A scalar
Herbie rewrite does not model their accumulation order or long-term numerical
error. These five outcomes do not justify claiming general phase 2 support or
selective mixed-precision recovery yet.

## Handoff

All five replacement tasks completed; no native or remote work remains active.
All declared attempts are exhausted. Do not retry or replace this cohort in
place. Any extension should freeze a new plan importing these exact sources and
retaining these baseline failures. Model budgets and accelerator usage remain
zero; final holdouts were not accessed. Nothing was pushed, so no remote CI or
hardware qualification is claimed.

Locked repository development checks passed: Ruff lint, formatting, strict mypy,
and pytest (**596 passed, 3 skipped**). The corrected experiment wrapper also
passed a direct strict mypy check and was exercised by all five replacement
tasks. These checks do not establish numerical or hardware correctness.
