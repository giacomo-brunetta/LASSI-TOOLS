---
name: lassi-collect-perf-stats
description: Collect microarchitectural counters per benchmark case and derive IPC + (where available) cache/branch metrics. Linux uses `perf stat`; macOS / Apple Silicon transparently falls back to `/usr/bin/time -l` and reports instructions, cycles, IPC, wall/user/sys time, RSS, page faults, and context switches (no cache/branch counters on this path). Use when wall-clock isn't enough.
allowed-tools:
  - Bash(python cli/lassi-collect-perf-stats.py*)
  - Bash(python3 cli/lassi-collect-perf-stats.py*)
  - Read
---

Wraps `perf stat -r <repeat>` around each case command and parses the results into the LASSI perf JSON schema. Differential mode pairs `command_a` and `command_b`.

**Platform note:** on macOS / Apple Silicon (no Linux `perf` binary) the impl transparently falls back to `/usr/bin/time -l`, looped `repeat` times. You get `instructions` + `cycles` (so IPC works), `wall_s/user_s/sys_s`, page faults, RSS, voluntary/involuntary context switches, and CV% across runs. **Branch and cache counters are absent** on this path — Instruments + elevated privileges would be needed for those.

## Invocation

```
python cli/lassi-collect-perf-stats.py \
    --cases '[...]'  |  --cases-file cases.json \
    [--mode single|differential] [--events '["cycles","instructions"]'] \
    [--repeat 5] [--timeout-s 600] [--artifact-dir DIR] [--no-json-output] [--shell bash]
```

## Example

```
python cli/lassi-collect-perf-stats.py --cases-file .perf/cases.json --repeat 7
```

## Underlying impl

`lassi.profiling.performance_tools.collect_perf_stats_impl`
