---
name: lassi-compare-performance
description: Aggregate prior benchmark, perf-stat, and hotspot JSON artifacts into a single differential performance verdict. Use after running the three collectors to render a final pass/regress/inconclusive judgement.
allowed-tools:
  - Bash(python cli/lassi-compare-performance.py*)
  - Bash(python3 cli/lassi-compare-performance.py*)
  - Read
---

Reads any combination of `run_benchmark` / `collect_perf_stats` / `profile_hotspots` result JSONs and applies the comparison policy (effect-size thresholds, CV bounds, etc.) to emit a verdict.

## Invocation

```
python cli/lassi-compare-performance.py \
    [--benchmark-result-path PATH] [--perf-stats-result-path PATH] [--profile-result-path PATH] \
    [--policy '{"min_effect_size_pct":1,"max_cv_pct":5}' | --policy-file policy.json] \
    [--artifact-dir DIR]
```

## Example

```
python cli/lassi-compare-performance.py \
    --benchmark-result-path .perf/bench.json \
    --perf-stats-result-path .perf/stats.json
```

## Underlying impl

`lassi.profiling.performance_tools.compare_performance_impl`
