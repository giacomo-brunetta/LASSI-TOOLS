# Campaign workflow

New campaigns use `lassi-x campaign`. A campaign is a frozen plan of named tasks,
with explicit inputs, gates and attempt budgets. The runner owns the handoffs;
stage adapters own generation, scientific validation, repair and measurement.
The existing single-run `lassi-x run` pipeline remains available. The historical
launchers under `experiments/` have **not** been converted into stage adapters.
Their directory scanning and continuation rules are not the new campaign protocol.

## Scientific stages

Use this sequence when designing a campaign:

1. **Generate:** create candidate revisions with fixed model and correction budgets.
2. **Validate:** run the full CPU correctness suite and the configured LLM judge.
3. **Adapt:** create a new revision for a different workload, precision or target.
4. **Validate:** check that revision on the actual target workload, including input
   semantics, numerical accuracy, precision policy and execution limits.
5. **Repair:** create a child revision from a recorded failure, within a fixed budget;
   validate that revision again. Every changed revision needs its own evidence.
6. **Measure:** collect performance for an explicitly selected, validated revision.
7. **Audit:** use independent holdouts. Do not feed holdout failures back into the
   scored repair budget; a further repair belongs to a new experiment.
8. **Report:** select explicit result artifacts and retain all planned cases in the
   denominators, including failures, blocked cases and incomplete work.

These are stage labels, not inherited certifications. A passed generation task
does not certify correctness. A passed CPU test does not certify another dataset,
precision or device. The adapter implements the gate recorded in the plan.
Generation may be shared, but target branches and model repair branches receive
independent copies of the same selected starting revision and failure feedback.

Use `case` to identify a planned experimental cell, including model/replicate,
workload, target and precision as appropriate. Give each candidate slot and revision
its own task and named outputs when they need independent acceptance decisions.
Do not collapse "any candidate passed" and candidate pass fraction into one metric.

## Plan and commands

```sh
lassi-x campaign prepare campaign.yaml /path/outside/project/my-campaign
lassi-x campaign status /path/outside/project/my-campaign
lassi-x campaign run /path/outside/project/my-campaign
lassi-x campaign retry /path/outside/project/my-campaign --task target-check
lassi-x campaign run /path/outside/project/my-campaign
```

Preparation does not execute commands or contact models. It validates the whole
dependency graph, snapshots declared files and refuses an existing destination.
Commands execute only through `run` or `retry`. No shell expansion is performed.

A plan has this shape; `target_check.py` is a trusted adapter implementing your
recorded target gates, rather than a generated candidate:

```yaml
schema_version: 1
name: large-fp16-validation
methodology: Validate a frozen cohort on LARGE before measuring or repairing it.
protocol:
  workload: LARGE
  precision: fp16
  selection: All frozen candidate slots; no latency-based selection.
  environment: Record the code revision, locked dependencies and device/runtime versions here.
  gates:
    relative_l2_max: 0.01
    timeout_s: 120
    precision_policy: fp16-storage-fp32-accumulation
  model_budget: No model calls in this validation campaign.
files:
  adapter: target_check.py
  config: target.yaml
  source:
    campaign: /path/to/cpu-campaign
    task: cpu-check-c1
    attempt: 1
    output: candidate
tasks:
  - id: target-check
    case: terra-r1-three-mm-large-a100-fp16-c1
    stage: validate
    command: [python, "{input:adapter}"]
    timeout_s: 180
    max_attempts: 2
    checks: [input-semantics, numerical-suite, precision-policy, execution-limit]
    inputs:
      adapter: files/adapter
      config: files/config
      candidate: files/source
    outputs:
      candidate: {path: candidate.py, role: candidate}
      evidence: {path: target-check.json, role: evidence}
```

All local file paths resolve relative to the plan file during preparation. Adapters,
configs, references and helper files must be declared inputs to become snapshots.
Use `{input:name}` as an entire command argument to reference a copied input.
The command executable and installed packages come from the runner environment;
freeze that environment separately with the lockfile/container and record it in
the protocol. Keep credentials in the environment rather than in plan files.

Within one plan, a measurement task can declare:

```yaml
dependencies:
  target-check: [passed]
inputs:
  candidate: target-check/candidate
  validation: target-check/evidence
```

Other command inputs, output declarations and planned checks are still required.
A repair task can explicitly accept `[failed]` from a validation dependency.
`incomplete` means the evidence could not establish the gate; it is not a numerical
failure and is not accepted by default. A missing required artifact blocks the
consumer even when the dependency's outcome is allowed.

Prefer separate frozen evaluation and repair plans when selecting a repair cohort
from completed results. Import exactly the failed revisions and feedback selected
by the recorded policy. A plan is a finite graph; it does not discover new tasks,
pick a best candidate, merge conditional branches or search old campaigns.

## Stage adapter interface

The runner sets `LASSI_CAMPAIGN_CONTEXT` to a JSON file. Adapters can use:

```python
from lassi_x.campaign import Check, StageContext, Verdict

context = StageContext.load()
candidate = context.input_path("candidate")  # Verifies its recorded hash.
# Run the harness-owned checks and write the task's declared outputs in work_dir.
# Construct one Check for EVERY ID in context.task.checks from actual evidence.
checks = [Check(id="numerical-suite", status="passed", reason="All 12 tests passed")]
# This illustration assumes the task has exactly the numerical-suite check.
context.finish(Verdict(status="passed", reason="All planned checks passed", checks=checks))
```

For the plan above, report all four declared checks instead. Each check status is
`passed`, `failed`, `not_run` or `inconclusive`, with a reason. A positive verdict
requires **all** checks to pass. A failed verdict needs at least one failed check.
An incomplete verdict can preserve checks that passed alongside those that did not
finish. The runner retains them and fills missing results as inconclusive when a
process crashes or times out. A verdict omitting planned checks blocks advancement.

Write the verdict only after collecting evidence. Write declared artifacts inside
`context.work_dir`; `context.finish()` writes the verdict, not the artifacts.
A passing stage must produce every declared output. A failing stage may publish
the artifacts it has, such as the rejected revision and its diagnostics. Consumers
must explicitly request each artifact they need.

Adapters exit **zero** when they successfully report a scientific outcome, including
a negative verdict. A nonzero exit, missing/malformed verdict, timeout, changed
input or missing passing output makes the attempt incomplete. Candidate programs
must never be responsible for writing their own acceptance verdicts. The campaign
runner is orchestration, not a candidate sandbox; use the execution backends for
candidate isolation.

## Continuation and provenance

| Operation | Meaning |
| --- | --- |
| `run` | Execute ready tasks with no prior attempts; keep every previous result |
| `retry --task ID` | Repeat one failed/incomplete task on the same frozen inputs, within its attempt budget |
| Repair task | Change candidate code; produce a new artifact with parent hashes |
| New plan | Change methodology, selection, workload, gates, model budget or stage commands |

Retry does not continue downstream tasks automatically; use `run` afterward.
A passed task cannot be retried in place. If a downstream task has already run,
retrying its ancestor is refused: prepare a new campaign with explicit imports.
An interrupted attempt stays incomplete and requires an explicit retry. Runner
timeouts and handled interruptions kill the stage process group; hard termination
of the runner can leave external work requiring cleanup before retrying.

Imported artifacts name a **campaign, task, attempt and output**. They default to
requiring a passed source attempt. Use `accept: [failed]` explicitly when importing
a rejected revision for repair. The destination verifies the source record and
artifact, copies the bytes, and preserves its role and parent identity. The new
campaign no longer depends on the source directory remaining available. Importing
code does not import a correctness certificate for a new workload.

```text
my-campaign/
  plan.json, plan.sha256      frozen plan and input inventory
  files/                     copied starting inputs
  tasks/<task-id>/000001/
    context.json             exact input identities and stage protocol
    inputs/                  independent input copies
    work/                    adapter workspace and verdict.json
    stdout.log, stderr.log
    artifacts/               published output snapshots
    result.json, result.sha256
```

Status includes every planned task, its case, stage, attempt count, reason and
the outcome/checks of every prior attempt. A passing retry never hides a failure.
Blocked and unstarted tasks remain visible. Only one runner can execute a campaign
at a time. Changed plans, published artifacts, terminal records and gaps in attempt
history are rejected rather than silently reused. Hashes detect accidental changes;
they are not signatures or protection against an untrusted process with write access.

`run`/`retry` exit 0 when every `required: true` task has passed, 1 when some have
not, and 2 for invalid commands or campaign integrity errors. `required` defaults
to true. Set false for explicitly optional diagnostic/repair branches; this affects
the command exit code only and never removes their cases or failures from status.

## Migrating the old workflows

Keep old campaign evidence readable without replaying or rewriting it. For a new
scored campaign, write small adapters around the existing numerical, judge,
precision, holdout and measurement APIs. Replace directory searches with declared
inputs and replace launcher-specific retries with the runner's attempt policy.
Do not wrap an old launcher that still searches for "latest" results: that would
preserve the original ambiguity inside a new command.

The runner and stage interface are implemented and tested. Existing launchers have
not been automatically migrated, and no new scientific campaign has been executed
as part of this redesign. Multi-host scheduling and backend checkpoint recovery
remain responsibilities of the execution layer/adapters; this runner is sequential.
