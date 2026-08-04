# Paper benchmark suite

This suite runs the six PolyBench kernels and four scientific kernels identified by the
earlier LASSI breadth manifest. It validates FP64 semantic equivalence with the `mini`
profile on the local harness, measures accelerator accuracy on that same profile, and
times the `extralarge` profile on CUDA and Groq. Input construction, Academy transport,
PBS queueing, and MCP latency are outside the timed region.

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
python experiments/paper/run_suite.py
```

The runner performs one Academy execution doctor check, continues past individual kernel
failures by default, saves one full log per run, and writes a resumable JSONL journal
under `runs/paper-suite/`. Resume with `--resume PATH`. Use `--repetitions N` for repeated
model trials and `--kernel NAME` / `--model NAME` for a subset.

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
