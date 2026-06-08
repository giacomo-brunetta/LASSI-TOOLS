---
name: lassi-profile-hotspots
description: Sample runtime hotspots per benchmark case and report top-N functions; compare hotspot shifts between a/b variants. Linux uses `perf record/report/script` (with optional FlameGraph SVG); macOS / Apple Silicon falls back to `/usr/bin/sample` against the launched target's PID (no FlameGraph). Use when locating which functions dominate runtime, or how hotspots move after a change.
allowed-tools:
  - Bash(python cli/lassi-profile-hotspots.py*)
  - Bash(python3 cli/lassi-profile-hotspots.py*)
  - Read
---

Drives `perf record` at the configured sample frequency (default 999 Hz), processes the samples through `perf report`/`perf script`, and (optionally) generates a flamegraph SVG if `stackcollapse-perf.pl` and `flamegraph.pl` are on PATH.

**Platform note:** on macOS / Apple Silicon (no Linux `perf` binary) the impl launches the target as a subprocess and runs `/usr/bin/sample <pid> <duration>` against it. The call graph is parsed into the same `top_functions_<suffix>` shape Linux produces, so `compare_performance` and `hotspot_shift` work unchanged. `--no-callgraph`, `--frequency`, and `--generate-flamegraph` are ignored on macOS (sample has fixed 1ms sampling and no FlameGraph integration). Symbols resolve only when the target binary ships with debug info or is publicly symbolic — interpreted programs (Perl, Python, …) often show `???` because their hot frames live inside the interpreter's stubbed leaves.

## Invocation

```
python cli/lassi-profile-hotspots.py \
    --cases '[...]'  |  --cases-file cases.json \
    [--mode single|differential] [--no-callgraph] [--frequency 999] \
    [--timeout-s 600] [--generate-flamegraph] [--artifact-dir DIR] [--shell bash]
```

## Example

```
python cli/lassi-profile-hotspots.py --cases-file .perf/cases.json --generate-flamegraph
```

## Underlying impl

`lassi.profiling.performance_tools.profile_hotspots_impl`
