# Paper benchmark suite

This suite runs six upstream PolyBench kernels and five LASSI scientific kernels. It
validates FP64 semantic equivalence with the `large` profile on the local harness, then
uses that same `large` workload for paired device accuracy and latency on CUDA and Groq.
Input construction, Academy transport, PBS queueing, and MCP latency are outside the
timed region.

Every paper candidate is also screened against an explicit target compatibility snapshot before
it is finalized. Agents list published targets, select the closest exact Groq/compiler snapshot,
query expected `aten.*` operators at FP16, and report both the target and evidence. A canonical
operator compile narrows the risk but does not replace full-model GroqFlow compilation and LPU
measurement. The restored Torch-MLIR/TOSA corpus remains available only as a labeled legacy target.

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
The mutual-information baseline is versioned with this manifest under
[`examples/PolyBenchC-4.2.1/scientific/mutual-information`](../../examples/PolyBenchC-4.2.1/scientific/mutual-information)
and should be cited at the same LASSI-TOOLS revision as `benchmarks.yaml`. Its `large`
profile is the `256 x 256` joint-probability problem used by the standalone Groq example.
The complete paths, dimensions, live-outs, models, and source revisions are frozen in
[`benchmarks.yaml`](benchmarks.yaml).

Generate or refresh the checked-in configs:

```bash
conda activate LASSI
pip install -e '.[globus]'
lassi-x skills sync
lassi-x-compat-wiki targets
lassi-x-compat-wiki op aten.mm --target legacy-torch-mlir-tosa
python experiments/paper/generate_configs.py
```

### Generate a target compatibility wiki

Generation is split so every compiler probe runs directly in its vendor environment. First build
one canonical manifest from a Torch-MLIR checkout pinned to an exact commit:

```bash
lassi-x-compat prepare \
  --torch-mlir-root /path/to/torch-mlir \
  --revision <exact-git-sha> \
  --output /tmp/lassi-compat-manifest.json
```

Copy that manifest to the target machine and run the appropriate checked-in target configuration:

```bash
lassi-x-compat probe \
  --manifest /tmp/lassi-compat-manifest.json \
  --target compat_tool/targets/a100-sami-inductor.yaml \
  --run-dir compat-runs/a100 \
  --resume
```

Use `groq-r01-groqflow.yaml` on the Groq node. Each operator/precision cell is isolated and
checkpointed, so interrupted compiler sweeps resume safely. Back on the repository host, publish
the normalized JSON snapshot and independent Markdown wiki:

```bash
lassi-x-compat publish \
  --manifest /tmp/lassi-compat-manifest.json \
  --results compat-runs/a100/results.json \
  --output-root compat_tool
```

Publication writes partial diagnostics but exits nonzero until every included cell is either
`compiled`, `compile_rejected`, or honestly `not_applicable` to a floating-point profile. Raw
compiler logs and caches remain under ignored run directories.

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

Install
[`a100_compute_endpoint_user_config_template.yaml.j2`](a100_compute_endpoint_user_config_template.yaml.j2)
as `~/.globus_compute/lassi-x/user_config_template.yaml.j2` on `sami` before running the
suite, and restart the endpoint afterwards. The stock template cannot run this suite —
see [Wedged endpoints](#wedged-endpoints).

Override with `LASSI_PAPER_GPU_ENDPOINT=<uuid>`. `LASSI_PAPER_GPU=local` falls back to the
machine's own GPU and renames the backend to `harness-cuda` — use it for smoke tests only.
The two devices produce different timings and must never be pooled in one table, which is
why the backend name changes with the target.

### The Groq endpoint

The Groq leg needs a Globus Compute endpoint that nothing in the repo can start for you.
There are two supported placements, selected with `LASSI_PAPER_GROQ_MODE`.

**`direct` (default)** — the endpoint runs on a compute node that owns the LPUs, so
the measurement worker executes in place and PBS is not involved at all. Copy
`groq_compute_endpoint_user_config_template.yaml.j2` to
`~/.globus_compute/lassi-x-compute/user_config_template.yaml.j2` on the node, then:

```bash
ssh groq-r01-gn-01.ai.alcf.anl.gov
conda activate lassi-globus-compute
env -u PYTHONPATH globus-compute-endpoint start lassi-x-compute   # note the UUID
```

It is a user-config template, not a `config.yaml`. Recent endpoint releases render a
per-user endpoint process (UEP) from a template even when the endpoint is not multi-user
— both LASSI endpoints report `multi_user: false`. Its `config.yaml` holds only
endpoint-wide settings and refuses to start if it contains an `engine` block
(`endpoint will not start ... move the engine block to user_config_template.yaml.j2`).
Leave `config.yaml` as configured.

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

Direct mode is the default and already points at the registered compute endpoint
(`428a680f-1efb-488e-9558-96eb7f54a910`), so no variable is needed. Override only if the
endpoint is re-registered with a new UUID:

```bash
export LASSI_PAPER_GROQ_ENDPOINT=<uuid from the compute node>
```

**`pbs` (opt in)** — the endpoint runs on a login node, which has no LPUs, so every
measurement is submitted with `qsub` and waits in the batch queue:

```bash
export LASSI_PAPER_GROQ_MODE=pbs
conda activate lassi-globus-compute
globus-compute-endpoint start lassi-x
```

PBS mode has a known failure shape: the `qsub` call blocks inside the worker, and an
endpoint with a single worker then leaves every later task at `waiting-for-ep` while
still reporting `status: online`. `submit_timeout_s` (300s) bounds staging and submission
locally so an affected cell fails with a note naming the stalled stage instead of burning
the full `timeout_s`. Direct mode removes the cause rather than the symptom.

Set `LASSI_PAPER_GROQ=0` to generate a CUDA-only matrix and skip the leg entirely.

### Wedged endpoints

`status: online` is only a heartbeat from the endpoint *manager*. It says nothing about
whether a user endpoint process (UEP) exists to claim work. The failure to recognise is a
submitted task that stays at `waiting-for-ep` indefinitely while the endpoint reports
`online`:

```bash
python - <<'EOF'
from globus_compute_sdk import Client, Executor
import time
c = Client()
ex = Executor(endpoint_id="<uuid>", client=c)
f = ex.submit(lambda: "alive")
while not getattr(f, "task_id", None):
    time.sleep(1)
for _ in range(6):
    print(c.get_task(f.task_id)["status"]); time.sleep(5)
EOF
```

`waiting-for-ep` for more than a few seconds on an idle endpoint means the UEP is gone or
stuck. The cure is a manager restart on the node (`globus-compute-endpoint stop <name>`
then `start <name>`); the prevention is installing the user-config templates above, which
unset `idle_heartbeats_soft`, pin `min_blocks: 1`, and raise `max_workers_per_node`.

If the endpoints are restarted from somewhere other than this harness, leave

```bash
bash experiments/paper/wait_and_launch.sh
```

running here: it polls `--doctor-only` and launches the suite on the first pass. It never
touches an endpoint itself. Extra options are forwarded to the launcher.

The stock template's defaults are actively incompatible with this suite. LASSI launches
one long-lived `ExecutionAgent` per resource and keeps it for the whole run — every tool
call and measurement is an Academy round trip to that agent, not a fresh Globus task. With
`max_workers_per_node: 1` the agent occupies the resource's only worker; with
`idle_heartbeats_soft: 10` the UEP self-terminates after roughly five idle minutes, which
is shorter than the gap between measurements, killing the agent mid-run.

A response that dies with its agent never arrives, and Academy imposes no deadline on one.
`execution.call_timeout_s` (default 300 s) now bounds every Academy round trip on top of a
command's own `timeout_s`, so an unreachable agent fails the affected cells as `TIMEOUT`
with `execution agent unreachable` in the notes instead of hanging the run. Set
`LASSI_LOG_LEVEL=DEBUG`, or pass `--log-level`, to raise the harness log level; at the
default `INFO` every remote call already logs its start, its resource, and a warning each
minute it stays unanswered:

```
remote call handshake on a100-node [021de32b] capability probe unanswered after 120s
```

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
