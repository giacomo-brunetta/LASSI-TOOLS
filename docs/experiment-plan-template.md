# Experiment plan and handoff template

Copy this document into the new experiment's documentation directory. Replace all
`TODO` fields before starting the corresponding work. This is a planning record,
not a runnable campaign YAML file. Follow the [driver guide](experiment-driver-guide.md)
and use [campaigns.md](campaigns.md) for the executable plan schema.

## Question and scope

- Experiment ID: TODO
- Question or hypothesis: TODO
- Intended comparison and primary metric: TODO
- Unit of analysis: TODO (candidate, kernel, implementation/target cell, or other)
- User-authorized work and exclusions: TODO
- Chosen interface: TODO (`lassi-x run`, frozen campaign with named adapters, or
  exact historical reproduction)
- Output root and plan location: TODO (explicit absolute paths)
- Current stage: TODO (prepared, executing, interrupted, completed, or incomplete)

## Reproducible environment

| Item | Identity or artifact |
| --- | --- |
| Harness Git commit and dirty patch, if any | TODO |
| Remote worker Git commit and dirty patch, if any | TODO |
| Lockfile hash and environment/container identity | TODO |
| Python, Torch, NumPy, Hermes, Academy, and Pydantic versions | TODO |
| Compiler/runtime versions and full C build flags | TODO |
| Host, accelerator model, physical device, and runtime/driver | TODO |
| Model endpoint and requested/resolved model IDs | TODO |
| Credential source names, without values | TODO |
| Preflight outputs and timestamps | TODO |

## Complete cohort and artifact identities

List every planned case, including cases expected to fail or be unsupported.
Expand this table or provide a versioned inventory and record its path/hash here.
Do not replace the inventory with a list of successful outputs.

| Case ID | Kernel | Implementation/source hash | Specialization | Dataset/input hash | Precision | Target/resource | Model/replicate | Parent artifact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

- Inventory path and hash: TODO
- Planned candidate count: TODO
- Planned kernel count: TODO
- Planned workload/precision/target cell count: TODO
- Rules for unsupported, blocked, missing, and interrupted cases: TODO
- Selection policy for repair and final holdout cohorts: TODO
- Paired-baseline policy and evidence of baseline validity: TODO

## Reference and candidate interface

- Original C/C++ sources, dependencies, and hashes: TODO
- Workload dimensions, iteration counts, constants, and C types: TODO
- Oracle build/run commands and expected output identities: TODO
- Determinism repetitions and checks: TODO
- Input path: TODO (explicit C fixture specification or historical trusted contract)
- Fixture/contract paths and hashes: TODO
- Candidate argument mapping, scalar parameters, and output ordering: TODO
- Read-only versus read-write input semantics: TODO
- Alternate-input validity constraints and C import support: TODO
- Separate contracts for CPU validation and device evaluation, if applicable: TODO
- Confirmation that all intended workers support this input interface: TODO

If a required adapter is missing, name it and the work needed before execution.
Do not silently switch input interfaces to bypass an unsupported path.

## Gates and outcomes

Use exact values and protocols. A label such as "correct" or "fast" is not a gate.

| Gate | Required evidence | Threshold/protocol | Outcome if unavailable |
| --- | --- | --- | --- |
| CPU semantics | C oracle and all development cases | TODO | TODO |
| Input semantics | Actual supplied values, shapes, dtypes, scalar counts, mutation checks | TODO | TODO |
| Optional semantic judge | Model identity, evidence hash, structured verdict | TODO or explicitly disabled | TODO |
| Target execution | Actual source/workload on named device | TODO | TODO |
| Target accuracy | Named error metric, per-output handling, finite-output checks | TODO | TODO |
| Precision policy | Source/profile-bound audit and allowed arithmetic | TODO | TODO |
| Performance | Clock, residency, warmup, invocations/sample, sample count, statistic | TODO | TODO |
| Final holdout | Frozen sources, untouched policy, all cases and canonical control | TODO or explicitly outside scope | TODO |

- Run-level required backends and precisions: TODO
- Screening/pruning policy and whether it changes reported denominators: TODO
- Numerical improvement and non-regression requirements: TODO
- Scope of claims when only some gates pass: TODO

## Finite budgets and resource ownership

| Budget | Limit | What consumes it | What happens at exhaustion |
| --- | --- | --- | --- |
| Initial implementations and replicates | TODO | TODO | TODO |
| Planner format retries | TODO | TODO | TODO |
| Candidate correction rounds | TODO | TODO | TODO |
| Numerical compensation branches/rounds | TODO | TODO | TODO |
| Target compatibility branches/rounds | TODO | TODO | TODO |
| Model turn duration and transport retries | TODO | TODO | TODO |
| Campaign task attempts | TODO | TODO | TODO |
| Command, compile, and suite timeouts | TODO | TODO | TODO |
| Total model cost/token or experiment wall-time limit | TODO | TODO | TODO |

Record which limits the runner enforces and which the driver must monitor.
Do not assume a campaign attempt limit also caps nested model or repair attempts.

- Concurrent candidate flows: TODO
- Concurrent model sessions: TODO
- Per-resource capacity: TODO
- Cross-driver device lease or site-scheduler ownership: TODO
- Resource aliases that refer to the same physical device: TODO
- Job/request/PID tracking location: TODO
- Stop and cleanup procedure: TODO

## Commands and launch record

Write complete commands with actual paths. Keep preparation, preflight, execution,
and continuation separate. Record the directory emitted by the CLI immediately.

```sh
# Environment and preflight:
# TODO

# Preparation only, if using the frozen campaign runner:
# TODO

# Execution command and log destination:
# TODO

# Exact continuation/retry command, if needed:
# TODO
```

- Launch timestamp and driver host: TODO
- Configuration/plan path and hash: TODO
- Run or campaign directory: TODO
- Driver PID/session or scheduler job identity: TODO
- Full log artifact and bounded status view: TODO
- Evidence that no conflicting driver owns these resources: TODO

## Results and denominators

| Outcome | Candidate count | Kernel count | Workload/precision/target cell count | Evidence path |
| --- | --- | --- | --- | --- |
| Planned | TODO | TODO | TODO | TODO |
| Executed | TODO | TODO | TODO | TODO |
| Passed the stated gates | TODO | TODO | TODO | TODO |
| Scientific failure | TODO | TODO | TODO | TODO |
| Infrastructure/incomplete | TODO | TODO | TODO | TODO |
| Unsupported | TODO | TODO | TODO | TODO |
| Blocked or unstarted | TODO | TODO | TODO | TODO |

- Initial and retry outcomes retained at: TODO
- Accepted revision/source identities: TODO
- Numerical errors, latency samples, timing scope, and precision evidence: TODO
- Cohort exclusions and their predeclared justification: TODO
- CPU-only versus target-validated versus held-out claims: TODO
- Plots/frontiers and the exact eligible input records: TODO
- Limitations and unverified claims: TODO

These are separate views, not necessarily mutually exclusive totals. Define how
attempt outcomes reduce to case outcomes. Explain overlaps such as an unsupported
cell being included in the incomplete count. Report "at least one candidate passed"
and candidate pass fraction separately.

## Handoff to the next agent

- Last completed action and evidence: TODO
- Next unresolved gate and affected case IDs: TODO
- Exact continuation command: TODO
- Remaining budgets, including previous attempts and spend: TODO
- Active remote jobs, request IDs, PIDs, and resource owner: TODO or explicitly none
- Ambiguous submissions needing reconciliation before any retry: TODO or none
- Source/configuration/fixture changes since launch: TODO or none
- Files that must remain untouched: TODO
- Development feedback already exposed to agents: TODO
- Final holdout policy and whether it remains independent: TODO
- Code checks performed, actual hardware checks, and CI commit/result if pushed: TODO
- Known missing adapters or unsupported interfaces: TODO
