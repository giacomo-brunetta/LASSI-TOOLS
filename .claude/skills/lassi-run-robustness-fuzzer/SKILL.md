---
name: lassi-run-robustness-fuzzer
description: Build a libFuzzer target from a C/C++ source that defines `LLVMFuzzerTestOneInput`, run it with sanitizers, and persist the corpus + any crashing inputs. Use when verifying that a candidate doesn't crash, OOB, or trip UB on adversarial input.
allowed-tools:
  - Bash(clang *)
  - Bash(clang++ *)
  - Bash(mkdir *)
  - Bash(./*)
  - Read
---

libFuzzer is a coverage-guided fuzzer linked into clang. The target source must define:

```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) { ... return 0; }
```

## Two-step invocation

```bash
# 1. Build with libFuzzer + sanitizers + coverage instrumentation
mkdir -p .verify/corpus/fuzz/source build/fuzz
clang -O1 -g -fno-omit-frame-pointer \
      -fsanitize=fuzzer,address,undefined \
      fuzz/foo_fuzz.c -o build/fuzz/foo

# 2. Run with budget; corpus dir is the *first positional arg*
./build/fuzz/foo .verify/corpus/fuzz/source \
    -max_total_time=120 -max_len=4096 -jobs=4 -workers=4
```

## Tunable budget flags

- `-max_total_time=<sec>` — wall-clock budget.
- `-runs=<N>` — alternative: stop after N executions.
- `-max_len=<bytes>` — cap individual input size (default 4096).
- `-jobs=<N> -workers=<N>` — parallel fuzz jobs.
- `-seed_inputs=path1,path2` or pass a seed corpus dir as an extra positional arg before the main corpus dir.

## Interpreting output

- libFuzzer writes corpus units to the corpus dir, named by their SHA1.
- A crashing input is dumped as `crash-<hash>` in CWD; ASan/UBSan diagnostics print to stderr immediately before the crash file is written.
- Exit code 0 = budget exhausted with no crashes; non-zero = sanitizer hit or libFuzzer assertion.

## Caveats

- libFuzzer is **Linux-first**. On macOS it works with Apple-clang for `address,undefined`, but `fuzzer` linkage requires LLVM clang from Homebrew (`brew install llvm`) — not Apple-clang.
- Don't share a corpus dir between source-only and differential fuzz runs; keep them in separate paths (e.g. `.verify/corpus/fuzz/source` vs `.verify/corpus/fuzz/differential`).
