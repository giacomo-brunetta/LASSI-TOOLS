---
name: lassi-run-benchmark
description: Run stable timing benchmarks with hyperfine over one or more cases (single or differential a/b), returning the common LASSI perf JSON schema. Use when the user wants statistically-stable timing, not a one-shot run.
allowed-tools:
  - Bash(python cli/lassi-run-benchmark.py*)
  - Bash(python3 cli/lassi-run-benchmark.py*)
  - Read
---

Drives `hyperfine` with warmup/min/max-runs control and packages the per-case results into the LASSI perf JSON schema. Differential mode compares `command_a` vs `command_b` per case.

Cases shape (`--benchmark-cases`):

```json
[
  {"case_id":"sgemm-512","command_a":"./baseline","command_b":"./candidate",
   "working_dir":".","environment":{"OMP_NUM_THREADS":"1"},"metadata":{}}
]
```

## Invocation

```
python cli/lassi-run-benchmark.py \
    --benchmark-cases '[...]'  |  --benchmark-cases-file cases.json \
    [--mode single|differential] [--warmup 3] [--min-runs 10] [--max-runs 100] \
    [--timeout-s 600] [--shell bash] [--no-export-json] \
    [--prepare-command CMD] [--cleanup-command CMD] [--artifact-dir DIR] \
    [--thresholds '{"min_effect_size_pct":1,"max_cv_pct":5}']
```

## Example

```
python cli/lassi-run-benchmark.py --benchmark-cases-file .perf/cases.json --mode differential
```

## Underlying impl

`lassi.profiling.performance_tools.run_benchmark_impl`
