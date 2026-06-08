---
name: lassi-gprof-profiling
description: Build a C/C++ program with gprof instrumentation, run it, and read out the flat profile + callgraph. Use when the user wants a quick function-level hotspot list for a small program.
allowed-tools:
  - Bash(gcc *)
  - Bash(g++ *)
  - Bash(nvcc *)
  - Bash(clang *)
  - Bash(clang++ *)
  - Bash(./*)
  - Bash(gprof *)
  - Read
---

`gprof` requires the program to be both **compiled and linked** with `-pg`, then run normally (which drops a `gmon.out` next to the working directory), then post-processed by the `gprof` binary against the executable.

## Three-step invocation

```bash
# 1. Compile + link with -pg (and your normal optimization)
gcc -pg -O2 src/foo.c -o build/foo

# 2. Run the program (any input). Produces gmon.out in CWD.
./build/foo <args>

# 3. Read the profile
gprof build/foo gmon.out > foo.gprof.txt
```

For multi-file builds, all `.c` files must be compiled with `-pg`:

```bash
gcc -pg -O2 src/main.c src/helper.c -o build/foo
```

For CUDA, use `nvcc -pg ...` (or compile host `.cc` with `-pg` and link separately).

## Reading the report

`gprof` output has two sections:
- **Flat profile** — self-time + call counts per function. Top of the list = hottest functions.
- **Call graph** — caller/callee fan-in / fan-out with cumulative time. Useful for finding which call paths drive the hot functions.

## Caveats

- `gprof` doesn't work for very short runs (sampling resolution is ~10ms). If the report shows `0.00` everywhere, the program is too fast — loop it or process a bigger input.
- On macOS recent toolchains have spotty gprof support; prefer Linux or use `lassi-profile-hotspots` (perf-based) when available.
- `-pg` perturbs timing; never use a gprof build to also measure wall-clock latency.
