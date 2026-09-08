# LASSI-X

LASSI-X is a clean Hermes-powered arena for translating scientific C/C++ kernels
to PyTorch, repairing independently generated candidates, compensating FP16/BF16 error,
and constructing latency-versus-error Pareto frontiers.

The authoritative oracle is always the original C/C++ reference executed with
64-bit floating-point. A PyTorch module is never used as its own semantic oracle.

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
lassi-x skills install
lassi-x skills doctor
```

Configure Hermes providers and credentials with `hermes model`. LASSI-X pins
`hermes-agent==0.19.0` and gives the planner, candidate arena, optional compatibility repair,
and compensation roles independent model selections.

## Development checks

Run the same quality gates used in CI before committing:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

## Run

Copy [examples/run.yaml](examples/run.yaml), set the project path, reference build/run
commands, models, and backends, then run:

```bash
lassi-x run my-run.yaml
```

One immutable directory is written beneath the configured `runs_dir`:

```text
runs/<timestamp>-<kernel>/
├── resolved-config.yaml
├── oracle/
├── workspaces/
├── diagnostics/
├── measurements.jsonl
├── frontier.json
├── visualizations/
│   ├── pareto-overall.svg
│   ├── pareto-<backend>.svg
│   ├── frontiers.json
│   └── manifest.json
├── pipeline-graph.mmd
├── run.json
└── summary.md
```

`workspaces/` holds one confined directory per agent role: `c1`–`c3` for the
arena candidates, one per portable numerical trunk, and one per target-specific compatibility
leaf. Agent sessions reach their
workspace only through a run-local MCP server whose tools execute on the
configured `execution` resources (in-process by default, Academy execution
agents in `academy` mode), with each Hermes session pinned to its workspace by
a connection header.

## Agent memory (optional)

Agents can store and recall long-term memories across runs through the Hermes
mem0 memory provider, backed by a self-hosted [Mem0](https://github.com/mem0ai/mem0)
server. Start the stack in [docker/mem0](docker/mem0/README.md) and add a
`memory` section to the run config:

```yaml
memory:
  enabled: true
  host: http://localhost:8888
  user_id: lassi-x
```

Memories are off by default; omitting the section (or `enabled: false`) keeps
every memory layer disabled and agents behave exactly as before. When enabled,
each role (`planner`, `c1`…`cN`, `compensation-*`) writes memories under its
own Mem0 `agent_id` inside the shared `user_id` scope. Verify storage with
`pytest -m mem0` (runs against the live stack) or the REST queries in the
stack README.

## Remote execution

> **Status: live-tested.** On August 3, 2026, the complete PolyBench 3mm flow ran
> end to end through the hosted Academy exchange on a Globus Compute endpoint with
> two NVIDIA A100 GPUs: oracle, three-candidate arena, validation, CPU/CUDA
> measurements, compensation, and frontier construction all completed. Run
> `lassi-x execution doctor` for each new endpoint before spending an allocation.
>
> **Groq status: previously live-tested.** On August 4, 2026, the complete three-candidate
> PolyBench 3mm flow also ran through Academy and Globus Compute endpoint
> `266f3128-cc9a-403e-ab61-9284ed57d54b`. LASSI-X submitted each Groq cell from
> the AI Testbed login node to an exclusive GroqRack PBS compute node, activated
> `groqflow` inside the job, and recorded SDK-measured device latency against the
> external C FP64 oracle. The stricter single-call protocol described below was added
> afterward and still needs one Groq hardware revalidation.

In `academy` mode with an `exchange_url`, resources carrying a Globus Compute
`endpoint_id` run on that endpoint: reference sources and fixtures are staged
into remote workspaces over the wire, candidate validation executes the runner
on the endpoint and fetches its output back, and validated modules are mirrored
into `workspaces/` for local measurement. Install the extra and verify
connectivity before a run:

```bash
pip install -e '.[globus]'
lassi-x execution doctor --config my-run.yaml
```

Two annotated examples cover a first remote deployment: the endpoint
configuration for the remote node (standalone and Slurm variants) in
[examples/globus-endpoint/config.yaml.example](examples/globus-endpoint/config.yaml.example),
and the matching harness-side run configuration in
[examples/run-remote-node.yaml.example](examples/run-remote-node.yaml.example).

The doctor launches one execution agent per resource and reports the measured
host facts (accelerators, toolchain, torch and lassi-x versions) that also land
in `run.json` provenance. The endpoint environment must pin the same `lassi-x`
version as the harness.

Measurement cells run on their resources too: each `measure.backends` entry may
name a `resource`, and the worker (with the candidate module, oracle output,
and fixture pushed into a per-variant measurement workspace) executes there,
judging device availability from the resource's measured handshake. Every
measurement records its `resource`, so the Pareto frontier can legitimately mix
points from different machines. Oracle builds still run on the harness machine.

### Groq login endpoint and PBS compute jobs

The Globus Compute endpoint runs on the Groq **login** node in an environment
containing LASSI-X, Academy, and Globus Compute. It must not activate `groqflow`:
Groq device libraries belong on the PBS compute node. Configure a Groq backend
with `resource` plus `pbs` to make the login-node execution agent stage inputs,
submit an exclusive job, and poll its result:

```yaml
execution:
  mode: academy
  exchange_url: https://exchange.academy-agents.org
  auth: globus
  resources:
    groq-login:
      endpoint_id: 266f3128-cc9a-403e-ab61-9284ed57d54b
      workspace_root: /home/gbrun/lassi-x-groq-academy

measure:
  backends:
    - type: groq
      name: groq-lpu
      resource: groq-login
      precisions: [fp16]
      pbs:
        qsub: /opt/pbs/bin/qsub
        select: select=1,place=excl
        conda_sh: /home/gbrun/miniconda3/etc/profile.d/conda.sh
        conda_env: groqflow
        python: /home/gbrun/miniconda3/envs/groqflow/bin/python
```

Start the endpoint on the login node, then run the doctor from the harness:

```bash
# Groq login node
conda activate lassi-globus-compute
globus-compute-endpoint start lassi-x

# Harness
lassi-x execution doctor --config examples/polybench-3mm/run-sol-groq.yaml
lassi-x run examples/polybench-3mm/run-sol-groq.yaml
```

Direct Groq measurements are serialized as complete stage-submit-poll
transactions because one long-lived Academy agent owns the login endpoint.
Reported `latency_s` comes only from `GroqModel.benchmark()` on the GroqRack. The same compiled
model and static inputs are invoked on the LPU for the paired oracle comparison; Globus, Academy,
PBS queueing, file transfer, and input construction are excluded.
The legacy shared-filesystem `queue_dir` mode remains available for standalone
workers.

### Architectural single-call latency

Accelerator Pareto points use one intentionally narrow metric,
`architectural-single-call-v1`: the warm latency of one complete execution of the candidate graph
on exactly one physical accelerator. Each reported sample contains exactly one invocation. The
primary result is the median of independent samples; the minimum and every raw sample are retained
as audit evidence. A long on-device loop divided by its iteration count is not accepted.

Compilation, scheduler/PBS/Slurm queueing, process startup, allocation, device attachment,
executable loading, input construction, and host-to-device and device-to-host transfers are all
outside the timer. Inputs must have reached the device when timing begins, and timing stops when
the canonical output is ready on the device. The output is copied back only afterward and compared
with the matching C FP64 oracle. Thus every performance point still carries accuracy measured from
the same executable and inputs, while transfer and orchestration time cannot leak into
`latency_s`. This is an architectural kernel comparison, not an end-to-end or MLPerf-style system
benchmark.

The four target clocks are:

- NVIDIA A100: the warmed forward is captured as one CUDA Graph outside the timer, then CUDA events
  surround one graph replay. CUDA synchronization finishes each event sample, but compilation,
  capture, Python dispatch, per-operation launch dispatch, and synchronization time are not part of
  the event interval.
- GroqCard: one `GroqModel.benchmark(repetitions=1)` call per sample, using its runtime latency.
  Compilation and the PBS transaction occur before sampling.
- Graphcore IPU: one PopTorch invocation with `deviceIterations(1)`, followed by
  `getComputeLatency()` for that invocation. The built-in standalone worker compiles and warms the
  executable before sampling.
- Cerebras WSE-3: a site worker must return a profiler or hardware-counter interval with the same
  boundaries. Job duration is explicitly invalid. LASSI-X will reject a record if the installed
  Cerebras stack cannot expose such a timer.

Accelerator workers must identify this protocol and report their timing boundary, native clock,
warmup count, raw samples, one invocation per sample, one physical device, device input/output
residency, and the excluded costs. Missing or inconsistent evidence produces
`failure_kind: incomparable_timing`, so a convenient host or job timer can never enter a Pareto
frontier. CPU points retain host-forward timing for local baselines, but are not evidence for this
cross-accelerator architectural metric. Whenever architectural accelerator points exist, the
global frontier is built only from that protocol; host points cannot dominate it. CPU-only runs
still receive their ordinary local frontier.

Graphcore and Cerebras use `type: native` backends. The Graphcore worker ships with LASSI-X;
`worker.python` names the Python interpreter in the enabled Poplar SDK environment. Cerebras
requires a harness-local standalone script because WSE execution/profiling APIs depend on the
installed SDK and programming model; the script is staged to the selected resource and must emit
the same result schema.

```yaml
measure:
  warmup: 5
  iterations: 30
  backends:
    - type: torch
      name: a100
      device: cuda:0
      resource: polaris-a100
      precisions: [fp32, fp16, bf16]
    - type: groq
      name: groqcard
      resource: groq-login
      precisions: [fp16]
      pbs: # site settings omitted here
        conda_sh: /path/to/conda.sh
        python: /path/to/groqflow/bin/python
    - type: native
      name: graphcore-ipu
      architecture: graphcore_ipu
      resource: graphcore
      precisions: [fp32, fp16]
      worker:
        python: /path/to/poplar/python
    - type: native
      name: cerebras-wse3
      architecture: cerebras_wse3
      resource: cerebras
      precisions: [fp32, fp16, bf16]
      worker:
        python: /path/to/cerebras/python
        script: tools/cerebras_architectural_worker.py
```

## Flow

The orchestration state machine is defined with Pydantic Graph's typed
`GraphBuilder` API. `PipelineState` carries evolving experiment data, while
`PipelineDeps` injects immutable configuration and execution services. The
generated `pipeline-graph.mmd` records the exact left-to-right topology used by
the run, including the explicit compensation decision and bypass branch.

Every finalized run also creates self-contained, vector-native Pareto plots in
`visualizations/`. The overall plot compares all successful backend/device cells
and emphasizes the global frontier. Each backend plot recomputes the frontier
within that device only, so a useful GPU or Groq tradeoff remains visible even
when a small CPU kernel dominates it globally. SVG marker tooltips retain the
candidate, variant, resource, precision, compensation, latency, and error.
Color encodes backend in the overall view and precision in each device view;
marker shape encodes `variant_id` consistently across every plot in the run.
The exact color-independent shape mapping is stored in `manifest.json`.

1. Build and execute the original C/C++ FP64 oracle.
2. Ask a Hermes planner for `arena.candidates` materially distinct strategies.
3. Generate those candidates concurrently with separately configured models.
4. Validate each against the C/C++ FP64 oracle and apply bounded semantic repair turns.
5. Measure passing candidates across configured backend and precision cells. Each cell uses one
   evaluation workload for both latency and accuracy, and no latency is accepted without a
   finite output produced on that device and compared with the matching oracle.
6. Classify accelerator failures separately from numerical divergence. Group executable weak
   FP16/BF16 observations by candidate and precision, even when they came from different targets.
7. Create one portable numerical source trunk per group. It must pass the C/C++ FP64 oracle,
   collapse to base behavior at FP32, improve every weak target, and avoid regressing healthy
   targets. Failed gates are returned to the same agent session within its correction budget.
8. Broadcast every surviving numerical trunk across the full backend/precision matrix.
9. Only then fork immutable, target-specific compatibility leaves for compiler, whole-graph,
   placement, no-fit, or strict-precision failures. Each leaf starts from the base or portable
   numerical source that actually failed, uses the exact compatibility wiki, re-passes CPU FP64,
   and is remeasured on the real target. The leaf must preserve its parent's target accuracy when
   that accuracy exists; a newly executable leaf must meet the configured error threshold.
10. Construct the Pareto frontier using one configured scientific error metric and render overall
   and per-backend/device publication-ready SVGs.
11. Apply the run-level acceptance policy. By default every configured non-CPU backend must have
    a valid point; otherwise the run is `partial` even when CPU results exist.

Planner shape errors receive a bounded repair turn, and transient provider failures receive
bounded exponential backoff according to each model's `turn_retries` and `retry_*` settings.
Every Hermes turn also has a hard `turn_timeout_s` deadline. `models.candidates` must contain
exactly `arena.candidates` model entries.

Compensation defaults to points whose `max_rel_error` exceeds `error_threshold: 0.01`, even
when only one candidate survives. Set `compensation.error_metric` to `relative_l2`,
`max_abs_error`, or `invariant_error` when that is the scientifically relevant quantity.
Peer domination is same-candidate by default; cross-candidate selection must be requested
explicitly. One numerical variant is created per candidate/precision family rather than per
backend. The agent receives evidence and the capability intersection from every motivating
backend. A shared variant is promoted only if every weak cell improves and every already-healthy
cell at that precision does not regress; it is then measured across all configured cells.
`measurement_scope` remains accepted for older configurations, but portable variants are always
broadcast and new configurations should use `all`. Compiler/runtime crashes, unsupported
precisions, no-fit results, and infrastructure timeouts never enter numerical diagnosis; they are
handled later by independent compatibility branches.

The resulting source lineage is a tree rather than a set of unrelated target copies:

```text
c1  CPU-correct translation
├── n-c1-fp16  portable numerical trunk
│   ├── a-n-c1-fp16-groq-fp16  Groq-only compatibility leaf
│   └── a-n-c1-fp16-cuda-fp16  CUDA-only compatibility leaf
├── a-c1-groq-fp16  Groq-only compatibility leaf of the unchanged base
└── c1 remains available for the Pareto frontier
```

Compatibility changes are never propagated between platform leaves. Numerical changes are shared
as source first, but still require deterministic certification on every executable target.
`run.json` records promoted trunks under `numerical_candidates`, isolated leaves under
`compatibility_candidates`, and their `parent_candidate_id` links so the complete lineage can be
reconstructed without inferring it from filenames.

### Merged accelerator evaluation and success

The C/C++ oracle is executed twice by default (`oracle.determinism_runs`) and the source and output
hashes are recorded. Accelerator accuracy and performance are not separate tests: a cell has one
evaluation dataset, one source hash, one device execution path, one error bundle, and one latency.
Torch computes error from the final timed iteration's device output. Groq's benchmark API does not
return an output, so the worker evaluates the exact same compiled model and static input mapping on
the LPU and compares that result; both values remain part of one measurement transaction.

Every successful latency therefore carries `max_abs_error`, `max_rel_error`, `relative_l2`, and an
optional invariant from the same workload. Missing, non-finite, nondeterministic, or unverified
device output changes the cell to `diverged` with `failure_kind: missing_accuracy_latency_pair`.
If accelerator evaluation uses the CPU-validation dataset, it reuses the main oracle. Otherwise,
provide the matching evaluation oracle explicitly:

```yaml
oracle:
  determinism_runs: 2

measure:
  evaluation_dataset: large
  evaluation_oracle: fixtures/large-oracle.csv

compatibility:
  enabled: true
  correction_rounds: 2

pareto:
  # Omit to use compensation.error_metric.
  error_metric: relative_l2

success:
  # Omit required_backends to require every configured non-CPU backend.
  required_backends: [cuda, groq]
  required_precisions:
    cuda: [fp16]
    groq: [fp16]
```

The older `performance_dataset`, `performance_oracle`, `verify_performance_output`, and
`success.require_performance_verification` keys remain accepted for configuration compatibility.
They no longer create or disable a second test: output verification and the device
accuracy/latency pair are mandatory. New configurations should use `evaluation_dataset` and
`evaluation_oracle`. An explicit `required_backends: []` retains exploratory behavior where any
valid frontier point is enough. Compatibility repair uses `models.compatibility` when configured
and otherwise reuses the failed candidate's model.

Measurement status and `failure_kind` are deliberately separate. Status expresses the outcome;
the failure kind distinguishes precision/resource unavailability, infrastructure/submission
timeouts, candidate loading or execution, accelerator compilation, numerical divergence, and
source-integrity failures. Only candidate-caused accelerator failures are eligible for source
repair.

`kernel.invariant` is optional and uses `module:function` syntax. The function receives
the flattened candidate and C-oracle NumPy arrays and returns either a scalar error or
a dictionary containing an `error` field. Set `kernel.invariant_threshold` to make it a
hard measurement gate.

Torch backends share one timing semaphore by default, preventing CPU and CUDA measurements
from perturbing each other through concurrent host-side work. Set
`measure.serialize_torch_backends: false` only when throughput matters more than timing
isolation. CUDA `latency_s` is the median CUDA-event duration around one captured forward replay;
input construction and Academy/MCP transport are excluded. CPU timing uses `time.perf_counter` and
is labelled separately. `worker_wall_s` remains nullable for artifact compatibility but is not
populated by Torch/Academy measurements.

## Hermes skills

Fifteen focused skills ship with the package. They wrap deterministic `lassi-x`
commands and are installed only into the LASSI-X subtree of the selected Hermes home.
Use `lassi-x skills sync` after upgrades and `lassi-x skills uninstall` to remove only
manifest-owned files.

`lassi-x-accelerator-compatibility` gives planners family-level Graphcore, Cerebras CS-3,
and GroqFlow coverage and portable-core evidence. Candidate coders use the same skill to route
function-level decisions to the exact target compatibility wiki instead of copying the catalog
into agent instructions.

Low-precision work is split into diagnosis and intervention. `lassi-x-fp-error-diagnose`
localizes range, significance, cancellation, conditioning, function, and nondeterminism failures;
`lassi-x-fp16-compensate` selects and validates an intervention. The separate
`lassi-x-elementary-function-audit` prevents bounded approximations, finite sweeps, and correctly
rounded implementations from being treated as equivalent claims. The literature review and
technique backlog are in [docs/fp-error-literature.md](docs/fp-error-literature.md).

## Useful commands

```bash
lassi-x inspect machine
lassi-x inspect gpu
lassi-x inspect toolchain
lassi-x output summarize --path output.csv
lassi-x output compare --reference oracle.csv --candidate candidate.npy
lassi-x validate candidate --config run.yaml --module candidate.py --artifact-dir check
lassi-x benchmark run --config run.yaml --module candidate.py --backend cuda --precision fp16
lassi-x pareto build --measurements measurements.jsonl --output frontier.json
lassi-x pareto visualize --measurements measurements.jsonl --output-dir visualizations
lassi-x report verification --run runs/<run>
```

For the legacy shared-filesystem Groq mode, use:

```bash
lassi-x groq worker --queue-dir /shared/lassi-x-groq --executor \
  python /path/to/groq_executor.py --request-id '{request_id}' --module '{module_path}'
```

The worker publishes a queue heartbeat. Pipeline submissions fail fast when it is absent or
stale, and abandoned pending/running requests are converted to timeout completions after the
backend's `stale_request_s` interval.

## Trust boundary

This is a trusted research tool, not an adversarial-code sandbox. Workspace APIs reject path
traversal and measurements verify staged source hashes, but Hermes agents have terminal tools and
generated Python is imported and executed in subprocesses. The candidate currently owns
`build_inputs`, and no sealed holdout suite is generated automatically. `run.json` records these
facts under `evaluation` rather than claiming a stronger guarantee.

For an evaluation in which cheating must be impossible, run candidate generation and execution in
an externally isolated container or restricted account with no network, mount candidate source
read-only, keep acceptance fixtures and oracle outputs outside that namespace, and use fresh
holdouts after the repair session closes. A sealed evaluation oracle is compared with output from
the same device workload used to obtain latency, so every accepted performance point carries its
own device-derived accuracy result. Child processes are isolated into process groups and cleaned up on handled
timeout/shutdown; no in-process code can guarantee cleanup if the orchestrator receives `SIGKILL`.

## PolyBench 3mm reproduction

The former LASSI-TOOLS MINI 3mm arena has a dedicated reproduction under
[`examples/polybench-3mm`](examples/polybench-3mm). It preserves the three
candidates and two repair turns, uses a high-fidelity serialization of the
original C FP64 oracle, and measures CPU and CUDA low-precision error.
