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
`hermes-agent==0.19.0` and gives the planner, candidate arena, and compensation
roles independent model selections.

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
├── run.json
└── summary.md
```

`workspaces/` holds one confined directory per agent role: `c1`–`c3` for the
arena candidates and one per compensation variant. Agent sessions reach their
workspace only through a run-local MCP server whose tools execute on the
configured `execution` resources (in-process by default, Academy execution
agents in `academy` mode), with each Hermes session pinned to its workspace by
a connection header.

## Remote execution

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

## Flow

1. Build and execute the original C/C++ FP64 oracle.
2. Ask a Hermes planner for `arena.candidates` materially distinct strategies.
3. Generate those candidates concurrently with separately configured models.
4. Validate each against the C/C++ FP64 oracle and apply up to two repair turns.
5. Measure passing candidates across configured backend and precision cells.
6. Apply hardware-aware compensation to weak FP16/BF16 points.
7. Gate compensation against the C/C++ FP64 oracle and base PyTorch FP32 behavior.
8. Measure surviving variants and construct the Pareto frontier.

Planner shape errors receive a bounded repair turn, and transient provider failures receive
bounded exponential backoff according to each model's `turn_retries` and `retry_*` settings.
Every Hermes turn also has a hard `turn_timeout_s` deadline. `models.candidates` must contain
exactly `arena.candidates` model entries.

Compensation defaults to points whose `max_rel_error` exceeds `error_threshold: 0.01`, even
when only one candidate survives. Set `compensation.error_metric` to `relative_l2`,
`max_abs_error`, or `invariant_error` when that is the scientifically relevant quantity.
Peer domination is same-candidate by default; cross-candidate selection must be requested
explicitly. Variants are measured only in their motivating cell unless `measurement_scope:
all` is selected, and a variant that does not improve the targeted error is rejected.

`kernel.invariant` is optional and uses `module:function` syntax. The function receives
the flattened candidate and C-oracle NumPy arrays and returns either a scalar error or
a dictionary containing an `error` field. Set `kernel.invariant_threshold` to make it a
hard measurement gate.

Torch backends share one timing semaphore by default, preventing CPU and CUDA measurements
from perturbing each other through concurrent host-side work. Set
`measure.serialize_torch_backends: false` only when throughput matters more than timing
isolation. `latency_s` contains the warmed kernel median; `worker_wall_s` separately records
cold subprocess startup, Torch/CUDA initialization, warmup, and measurement overhead.

## Hermes skills

Twelve focused skills ship with the package. They wrap deterministic `lassi-x`
commands and are installed only into the LASSI-X subtree of the selected Hermes home.
Use `lassi-x skills sync` after upgrades and `lassi-x skills uninstall` to remove only
manifest-owned files.

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
lassi-x report verification --run runs/<run>
```

On a Groq-connected host, use:

```bash
lassi-x groq worker --queue-dir /shared/lassi-x-groq --executor \
  python /path/to/groq_executor.py --request-id '{request_id}' --module '{module_path}'
```

The worker publishes a queue heartbeat. Pipeline submissions fail fast when it is absent or
stale, and abandoned pending/running requests are converted to timeout completions after the
backend's `stale_request_s` interval.

## Trust boundary

This is a trusted local research tool, not a sandbox. Hermes agents have file/terminal tools,
and generated Python is imported and executed in subprocesses. Run only trusted configuration
and source inputs, do not expose the runner as a network service, and use an external container
or restricted account when stronger isolation is required. Child processes are isolated into
process groups and cleaned up on handled timeout/shutdown; no in-process code can guarantee
cleanup if the orchestrator itself receives `SIGKILL`.

## PolyBench 3mm reproduction

The former LASSI-TOOLS MINI 3mm arena has a dedicated reproduction under
[`examples/polybench-3mm`](examples/polybench-3mm). It preserves the three
candidates and two repair turns, uses a high-fidelity serialization of the
original C FP64 oracle, and measures CPU and CUDA low-precision error.
