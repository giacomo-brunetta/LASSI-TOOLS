# Five unchanged Torch models through the Herbie adapter

## Question and scope

- Experiment ID: `herbie-five-torch-20261104`.
- Question: can the deterministic Herbie expression adapter extract five existing
  scientific Torch models without rewriting their sources?
- User authorization: try five Torch models. No LLM calls, accelerator work,
  source adaptations or numerical acceptance claims are included.
- Intended comparison: source extraction support, one candidate per kernel.
- Interface: `lassi-x campaign`, five sequential capability-gate tasks.
- Output root: `/Users/giacomobrunetta/Projects/LASSI-TOOLS/runs/herbie-five-torch-20261104`.
- Plan: `campaign.yaml` in that root, SHA256
  `5626c08521d1fb352c21bfa1d57d684124b6263429d0bd71a48dac2416711b0d`.
- Current stage at plan creation: prepared, no tasks executed.

## Reproducible environment

The output root's `environment.json` records the exact harness commit, Python,
Torch, host, OS, lockfile, experiment adapter and Herbie adapter identities.
`working-tree.patch` preserves tracked changes; the campaign snapshots all
declared source files, including the untracked adapters. No environment upgrade
is authorized. No endpoint or credentials are used. No Racket or native Herbie
execution is part of this capability stage. Local CPU source parsing is the
only computational resource.

## Complete cohort and source identities

The fixed cohort is ATAX, GESUMMV, covariance, correlation and Deriche, using the
historical `c1-fp16.py` slots from
`runs/a100-full-large-revalidation-20261017/seeds/polybench-<kernel>/`.
These original run paths are not present locally. Their exact source bytes are
preserved in the explicitly named archive
`docs/experiments/input-integrity-audit-20261020/preliminary_inventory/source_index.json`.
The extraction verifies that each archived `source` reproduces its recorded
SHA256 before writing a snapshot. There is no selection by success, model
eligibility, directory recency or adapter outcome.

`cohort.json` records all five historical paths, classes, source hashes and the
archive hash. The runnable campaign's inputs are explicit files under `inputs/`.
They are historical evidence, not newly authored model implementations.

| Kernel | Class | Source SHA256 |
| --- | --- | --- |
| ATAX | ATAXModel | `8fdffd812018de0a56ffc0c2e4715180104b70c59a41b4d43d0c310851211973` |
| GESUMMV | GESUMMV | `f64df8dfa52461ab9def9be16dd5edf46b08cede5db52673dd3b2bba207f4b38` |
| Covariance | CovarianceModel | `786e457837c0cc1e8422c8f8a7a53bb51732411377389a09664aa9dcd0862fec` |
| Correlation | Correlation | `9e6b22a23b67602520926e90ce354dcd9d16e86dd6becafe8bce0e1a4c8b3628` |
| Deriche | Deriche | `b1581ec2151ceff48421ea60b89d9c4cd3b19959cea6801ae25a7a5916d955da` |

Planned denominators: five candidates, five kernels, five FP16 extraction cells.
There are zero planned numerical workload/device evaluation cells.

## Gates and outcomes

1. `frozen-inputs`: campaign input verification plus equality of the installed
   adapter and its snapshot, and equality of source bytes and the archive hash.
   An unavailable input or hash mismatch is incomplete, not unsupported.
2. `extraction-support`: call `lassi_x.herbie.extract` on the unchanged source,
   explicit class and `binary16` precision. A supported forward passes. An
   `UnsupportedExpressionError` fails with outcome `unsupported` and the exact
   diagnostic. Other crashes/timeouts remain incomplete.

Every task writes `evidence.json`, including static calls/methods, outcome and
diagnostic. No unknown source is imported or executed. All outcomes remain in
the denominator; no unsupported case is replaced.

Input fixtures, shapes, C compilation, CPU numerical semantics, same-source FP32
controls, execution precision, target validation, latency and final holdouts are
not evaluated at this stage. Historical `build_inputs` comments are not treated
as authoritative workload or validation evidence. A supported extraction alone
would still require a separately frozen input domain and C oracle before numerical
qualification. There is no scientific numerical threshold or model judge here.

## Finite budgets and ownership

- Five initial extraction attempts; one per named model, no retries or repairs.
- Thirty seconds per task, enforced by the campaign runner; 150 seconds of
  aggregate task budget, excluding runner setup/reporting.
- Sequential local tasks, no shared accelerator resources, no remote jobs.
- Zero model tokens/cost, zero native Herbie searches, zero accelerator jobs.
- Task process IDs and results are owned and retained by the campaign runner.
- On interruption, preserve the attempt and inspect status. Do not relaunch a
  second driver or retry without revising the declared zero-retry budget.

## Commands and artifacts

From `/Users/giacomobrunetta/Projects/LASSI-TOOLS`:

```sh
uv run --locked --extra dev --extra globus --extra roofline lassi-x campaign prepare \
  runs/herbie-five-torch-20261104/campaign.yaml \
  runs/herbie-five-torch-20261104/campaign
uv run --locked --extra dev --extra globus --extra roofline lassi-x campaign run \
  runs/herbie-five-torch-20261104/campaign
uv run --locked --extra dev --extra globus --extra roofline lassi-x campaign status \
  runs/herbie-five-torch-20261104/campaign
```

Preparation does not run the gates. Execution logs go to `campaign-run.log` in
the output root. Results retain the exact campaign/task/attempt identity and
per-model source snapshots. The human-readable report will distinguish actual
extraction attempts from Herbie searches and Torch executions. No accepted
candidate, speedup, mixed-precision repair or generalization claim is authorized
by these gates.

## Infrastructure recovery amendment

The first frozen campaign reached extraction but could not publish any verdict:
the experiment wrapper treated `StageContext.work_dir` as a `Path` although it
is a string. All five initial attempts remain `incomplete` in `campaign/`, with
their tracebacks. This was a reporting defect, not a numerical model result.

Correct only the wrapper's path conversion, preserving all five candidate bytes,
classes, extraction precision and adapter implementation. Freeze a new plan
`recovery.yaml` into `recovery-campaign/`, with one attempt per model and the same
30-second task limits. The amendment allows five replacement reporting attempts:
ten total wrapper invocations, at most 300 seconds of aggregate task budget,
zero model calls, zero native searches, zero accelerator jobs. No further retries
are planned. Both campaign identities must be included in the final report.
