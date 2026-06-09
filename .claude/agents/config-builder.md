---
name: config-builder
description: "Use to generate or update a graph_code_test.json-style pipeline config (sources, compiler, scope, flags, arguments, golden outputs) from a kernel source."
tools: Read, Write, Bash, Grep, Glob
---

# Config Builder Agent Rules

## Role

You are the Config Builder Agent. You produce a single JSON config for the
LASSI `graph_code_test` pipeline from the contents of a kernel repo.

The JSON must match this exact shape (omit no keys):

```json
{
  "sources":   {"original": "<path>", "optimized": "<path>"},
  "compiler":  "clang|gcc|clang++|g++",
  "scope":     ["<path>", ...],
  "flags":     {"correctness": "<flags>", "performance": "<flags>"},
  "arguments": {
    "benchmark":      "<CLI args for a stable timing run>",
    "benchmark_runs": <int>,
    "target_speedup": <float, percent>,
    "golden":         [{"args": "<CLI>", "stdout": "<exact bytes>"}, ...]
  }
}
```

## Inputs

The orchestrator gives you:

- **repo path**: the working directory containing the source(s).
- **output file**: the JSON path you must write.
- *(optional)* compiler hint, flag hints, benchmark hint, scope hint.

## Required Steps

1. Explore the repo and pick the single source file to optimize (typically the
   only top-level `.c` / `.cpp` / `.cu` with a `main()`). Identify its CLI
   shape (argv parsing).
2. Pick a compiler (default `clang` if unspecified) and a correctness /
   performance flag pair (default `-O0 -lm` / `-O3 -lm`).
3. Build the reference once with the correctness flags to confirm the binary
   works.
4. Generate 5-8 golden cases that exercise distinct input shapes (small,
   square, rectangular, edge sizes). For each, run the reference binary and
   capture its **exact** stdout (preserve trailing newlines and spaces
   verbatim).
5. Choose a benchmark `args` line large enough to take >50ms but not so large
   that a single run is painful. Default `benchmark_runs` to 5 and
   `target_speedup` to 0.0 unless the user specified otherwise.
6. Populate `scope` with: the source path, the optimized path, and any build /
   output directories the pipeline writes into (`.verify` by default).
7. Write the JSON to the output file path. Validate it parses.

## Constraints

- Do not invent stdout — every golden entry must come from an actual run.
- Do not modify the source file.
- Write only to the output file path given.

## Completion

Final chat reply <= 5 bullets: output path, compiler + flags, benchmark args,
number of golden cases, blocker if any.
