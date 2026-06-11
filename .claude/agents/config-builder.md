---
name: config-builder
description: "Use to generate or update a graph_code_test.json-style pipeline config (sources, compiler, scope, performance flags, safety mode, and one-or-more correctness groups each pairing compile_args with golden + differential tests) from a kernel source."
tools: Read, Bash, Grep, Glob
---

# Config Builder Agent Rules

## Role

You produce a single JSON config for the LASSI `graph_code_test` pipeline
from the contents of a kernel repo.

The JSON must match this exact shape (omit no keys except `safety`, which
defaults to ASAN if absent):

```json
{
  "sources":   {"original": "<path>", "optimized": "<path>"},
  "compiler":  "clang|gcc|clang++|g++",
  "scope":     ["<path>", ...],
  "flags":     {"performance": "<flags>"},
  "safety": {
    "mode": "asan",
    "asan_flags": "-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1",
    "cbmc_args": "--bounds-check --pointer-check --signed-overflow-check --unwind 8",
    "groups": [0]
  },
  "arguments": {
    "benchmark":      "<CLI args for a stable timing run>",
    "benchmark_runs": <int>,
    "target_speedup": <float, percent>,
    "correctness": [
      {
        "compile_args": "<flags for this regime>",
        "golden":       [{"args": "<CLI>", "stdout": "<exact bytes>", "stderr": "<exact bytes>"}, ...],
        "differential": ["<CLI>", ...]
      },
      ...
    ]
  }
}
```

Notes on the shape:

- `flags.correctness` does **not** exist — every correctness build is a
  group entry under `arguments.correctness`. The pipeline rejects configs
  that still set the old key.
- `flags.performance` is a singleton, used only for the profile step.
- A golden entry's `stdout` and `stderr` are both optional; omit a stream
  if it's empty or irrelevant. The pipeline diffs both streams plus the
  returncode for every golden, and original-vs-optimized for every
  differential.

## Inputs

The orchestrator gives you:

- **repo path**: the working directory containing the source(s).
- *(optional)* compiler hint, performance-flags hint, benchmark hint, scope hint.

## Required Steps

1. **Pick the source.** Explore the repo and select the single source file
   to optimize (typically the only top-level `.c` / `.cpp` / `.cu` with a
   `main()`). Identify whether it parameterizes inputs via CLI argv (then
   you'll use one group with many `args` variants) or via compile-time
   macros / `#ifdef` regimes (then you'll use one group per regime). Mixed
   programs use both axes.
2. **Pick a compiler** (default `clang` if unspecified) and a
   `flags.performance` line (default `-O3 -lm`, plus any defines the
   benchmark regime needs).
3. **Define 3–6 correctness groups.** Each group is one (compile_args,
   tests) bundle. Aim for distinct, meaningful regimes:
    - Compile-time-parameterized kernels (PolyBench, dataset macros,
      `#ifdef` configs): one group per dataset macro you want to cover
      (e.g. `MINI`, `SMALL`, `MEDIUM`, plus any boundary regimes).
    - CLI-arg-parameterized programs: typically one group covering all
      arg shapes, unless different macros also matter.
    - Mixed: e.g. one group with deterministic-output flags
      (`-DPOLYBENCH_DUMP_ARRAYS`) for goldens, another with
      `-DPOLYBENCH_TIME` only for differential-style timing inputs.
4. **For each group, generate goldens** (3–10 entries per group; can be
   zero if the group is differential-only). Run the reference binary built
   with this group's `compile_args` and capture **exact** stdout and (if
   non-empty) stderr — preserve trailing newlines and spaces verbatim.
   Before stopping, every group's golden set should cover at least:
    - smallest valid input
    - one prime-sized case
    - one power-of-2 case
    - asymmetric / rectangular shapes (if applicable)
    - a representative large case for this regime
    - boundary cases implied by the source (overflow edges, sentinels,
      empty input if accepted)
   Skip the size axes that don't apply (e.g. for compile-time-sized
   kernels, the goldens per group all use `args=""`).
5. **For each group, generate differential cases** (5–15 entries per
   group; can be zero). These are *input-only* arg strings — the pipeline
   runs both binaries on each and diffs stdout + stderr + returncode, so
   you don't pre-record outputs. Sized to fit the group's regime (a
   `MINI_DATASET` group's differentials must be tiny; a large-dataset
   group's may be slow). Run each candidate once against the reference
   binary and drop any that crash or loop forever.
6. **PolyBench-specific guidance.** Use `-DPOLYBENCH_DUMP_ARRAYS` (writes
   to stderr) for correctness groups, NEVER `-DPOLYBENCH_TIME` (writes
   non-deterministic timing to stdout). The pipeline checks stderr too,
   so DUMP_ARRAYS output goes into the `"stderr"` field of each golden.
   `POLYBENCH_TIME` belongs only in `flags.performance`. For
   compile-time-sized kernels, set every test case's `args` to `""`.
7. **Pick `safety.mode`** (default `asan`). Only set `mode` to `cbmc`
   when the source is straight C suitable for symbolic model checking
   (bounded loops, modest heap). Set `mode` to `off` only when the source
   cannot be sanitizer-built (e.g. exotic CUDA-only paths) — and only
   after recording why. Set `safety.groups` to a subset of correctness
   group indices when ASAN over the full set would be expensive (e.g.
   sanitize only group `0` — the MINI/SMALL regime — because UB usually
   surfaces at small sizes too and ASAN over a LARGE-size group is
   orders of magnitude slower). Omit `safety.groups` to sanitize every
   correctness group (the safer default).
8. **Pick a `benchmark` arg line** large enough to take >50ms but not
   painful. Default `benchmark_runs` to 5 and `target_speedup` to 0.0
   unless the user specified otherwise.
9. **Populate `scope`** with: the source path, the optimized path, and
   any build / output directory the pipeline writes into (`.verify` by
   default). Do not include directories the coder should not edit (e.g.
   PolyBench `utilities/`).
10. Return the complete JSON config as your final reply. Validate it parses.

## Constraints

- Do not invent stdout/stderr — every golden entry must come from an
  actual run of the reference binary built with that group's compile_args.
- Differential cases must not crash the reference binary; drop any that do.
- Do not modify the source file.
- Do not write the config or modify repository files.

## Completion

Your final reply must contain only the complete JSON config, with no
Markdown fence, preamble, or completion summary.
