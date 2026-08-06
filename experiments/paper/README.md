# Paper benchmark suite

This suite runs the six PolyBench kernels and four scientific kernels identified by the
earlier LASSI breadth manifest. It validates FP64 semantic equivalence with the `mini`
profile on the local harness, measures accelerator accuracy on that same profile, and
times the `extralarge` profile on CUDA and Groq. Input construction, Academy transport,
PBS queueing, and MCP latency are outside the timed region.

Every generated configuration explicitly sets `memory.enabled: false`. This keeps the
GPT-5.6 Sol and Claude Opus 5 trials independent: no agent recall is read or persisted
between kernels, models, candidates, or repetitions. Argo configs use its internal model
IDs (`gpt56sol` and `claudeopus5`), which support replaying Hermes tool-call history;
the suite directory names remain the friendly model labels.

The official kernels are from [PolyBench/C 4.2.1 beta](https://www.cs.colostate.edu/~pouchet/software/polybench/),
using the exact public source snapshot
[`3e872547`](https://github.com/MatthiasJReisinger/PolyBenchC-4.2.1/commit/3e872547cef7e5c9909422ef1e6af03cf4e56072).
The `scientific/` kernels are LASSI's PolyBench-conformant additions, not upstream
PolyBench; their exact cited source is LASSI-TOOLS commit
[`32f56a57`](https://github.com/giacomo-brunetta/LASSI-TOOLS/tree/32f56a571e91572ca94d15017279a3af37d5b68c/examples/PolyBenchC-4.2.1/scientific).
The complete paths, dimensions, live-outs, models, and source revisions are frozen in
[`benchmarks.yaml`](benchmarks.yaml).

Generate or refresh the checked-in configs:

```bash
conda activate LASSI
python experiments/paper/generate_configs.py
```

Preflight without spending model or accelerator time:

```bash
python experiments/paper/run_suite.py --dry-run
```

Run the full session (all GPT-5.6 Sol runs first, then all Claude Opus 5 runs):

```bash
bash experiments/paper/launch_suite.sh
```

### The GPU endpoint

CUDA measurements are timed on the two-A100 Globus Compute endpoint
(`b162a840-38b4-4c1a-84cc-579fb62f4dfc`), not on the machine driving the suite. The
backend is named `a100-cuda` and bound to resource `a100-node`; the oracle build/run and
every agent tool call stay on the local `harness` resource so the reference compile is
identical across the matrix.

Override with `LASSI_PAPER_GPU_ENDPOINT=<uuid>`. `LASSI_PAPER_GPU=local` falls back to the
machine's own GPU and renames the backend to `harness-cuda` — use it for smoke tests only.
The two devices produce different timings and must never be pooled in one table, which is
why the backend name changes with the target.

### The Groq endpoint

The Groq leg needs a Globus Compute endpoint that nothing in the repo can start for you.
There are two supported placements, selected with `LASSI_PAPER_GROQ_MODE`.

**`direct` (recommended)** — the endpoint runs on a compute node that owns the LPUs, so
the measurement worker executes in place and PBS is not involved at all. Copy
`groq_compute_endpoint_user_config_template.yaml.j2` to
`~/.globus_compute/lassi-x-compute/user_config_template.yaml.j2` on the node, then:

```bash
ssh groq-r01-gn-01.ai.alcf.anl.gov
conda activate lassi-globus-compute
env -u PYTHONPATH globus-compute-endpoint start lassi-x-compute   # note the UUID
```

It is a user-config template, not a `config.yaml`. The endpoint is multi-user: its
`config.yaml` holds only endpoint-wide settings and refuses to start if it contains an
`engine` block (`endpoint will not start ... move the engine block to
user_config_template.yaml.j2`). Leave `config.yaml` as configured.

`env -u PYTHONPATH` is required. GroqRack compute nodes export
`/opt/groq/runtime/site-packages` site-wide, and `PYTHONPATH` precedes an environment's own
`site-packages` on `sys.path`, so its stale `typing_extensions` shadows the conda env and
the endpoint fails to import (`cannot import name 'Sentinel' from 'typing_extensions'`).
Workers inherit the daemon's environment, so clearing it once at start covers everything.
The generated worker scripts clear it themselves as well.

The node runs the checkout at `/home/gbrun/LASSI-TOOLS/src`, not the one you launch the
suite from, so `git pull` there before a run. A stale checkout surfaces as a candidate
failing with `ModuleNotFoundError: No module named 'pydantic'` — the accelerator
environment is `groqflow`, which has torch but not the configuration stack, and older
`lassi_x/__init__.py` imported it eagerly.

```bash
export LASSI_PAPER_GROQ_MODE=direct
export LASSI_PAPER_GROQ_ENDPOINT=<uuid from the compute node>
```

**`pbs` (default)** — the endpoint runs on a login node, which has no LPUs, so every
measurement is submitted with `qsub` and waits in the batch queue:

```bash
conda activate lassi-globus-compute
globus-compute-endpoint start lassi-x
```

PBS mode has a known failure shape: the `qsub` call blocks inside the worker, and an
endpoint with a single worker then leaves every later task at `waiting-for-ep` while
still reporting `status: online`. `submit_timeout_s` (300s) bounds staging and submission
locally so an affected cell fails with a note naming the stalled stage instead of burning
the full `timeout_s`. Direct mode removes the cause rather than the symptom.

Set `LASSI_PAPER_GROQ=0` to generate a CUDA-only matrix and skip the leg entirely.

On the CUDA harness, activate the `LASSI` environment and ensure the Globus client extra
is installed with `pip install -e '.[globus]'`. The launcher regenerates every config and
performs one Academy execution doctor check before spending model or accelerator time. Use
`bash experiments/paper/launch_suite.sh --doctor-only` to validate the endpoint setup
without launching an experiment.

The runner continues past individual kernel failures by default, saves one full log per
run, and writes a resumable JSONL journal under `runs/paper-suite/`. Resume with
`--resume PATH`. Use `--repetitions N` for repeated model trials and `--kernel NAME` /
`--model NAME` for a subset.

Each run is bounded by `--run-timeout-s` (default 7200, matching the measurement backend
ceiling; `0` disables it). On expiry the runner signals the child's whole process group —
reaping MCP servers and Academy agents along with it — and journals `timed_out: true`
rather than stalling the remaining matrix. A run that already emitted a successful result
envelope and then hung only in teardown is journaled as a success with
`teardown_hang: true`, so its artifacts still count and `--resume` will not repeat it.

Aggregate the journal's candidate pass rates and kernel solve rates with:

```bash
python experiments/paper/summarize_suite.py runs/paper-suite/session-....jsonl
```

Each `run.json` now records initial and final candidate pass rates, repair recovery, and
arena pass@k estimates. These are useful operational metrics, but the three candidates
receive distinct planner strategies and are therefore not IID samples. A canonical
pass@k claim requires multiple independent, identically prompted generations per
model/kernel (and preferably counterbalanced model order), which this runner supports
through repetitions but does not pretend the strategy-diverse arena already provides.
