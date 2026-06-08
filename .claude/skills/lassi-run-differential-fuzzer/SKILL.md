---
name: lassi-run-differential-fuzzer
description: Run an existing differential libFuzzer binary (one that calls both reference and candidate inside `LLVMFuzzerTestOneInput` and aborts on divergence) and persist corpus + divergent inputs. Use as the deepest equivalence check, after random equivalence tests.
allowed-tools:
  - Bash(mkdir *)
  - Bash(./*)
  - Read
---

The fuzz target source itself must implement the differential check, e.g.:

```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    double x;
    if (size < sizeof(x)) return 0;
    memcpy(&x, data, sizeof(x));
    double a = ref_kernel(x);
    double b = cand_kernel(x);
    if (fabs(a - b) > 1e-9) abort();
    return 0;
}
```

Compiled with `clang -fsanitize=fuzzer,address,undefined` (see `lassi-run-robustness-fuzzer` for the build pattern).

## Invocation

```bash
mkdir -p .verify/corpus/fuzz/differential
./build/fuzz/foo_diff .verify/corpus/fuzz/differential \
    -max_total_time=120 -max_len=4096 -jobs=4 -workers=4
```

If you have a seed corpus to mine first, pass it as an extra positional dir **before** the main corpus:

```bash
./build/fuzz/foo_diff .verify/corpus/fuzz/seed .verify/corpus/fuzz/differential \
    -max_total_time=120
```

## Interpreting output

- Divergent inputs are saved as `crash-<hash>` (because the target `abort()`ed on disagreement) in CWD.
- Each unit in the corpus dir is a coverage-novel input that did **not** diverge — keep it as seed corpus for the next run.
- Exit code 0 = budget exhausted with no divergence; non-zero = a divergence was found.

## Recommended workflow

1. `lassi-run-random-equivalence-tests` first (broad, fast).
2. Move any minimized counterexamples into the differential fuzz seed corpus.
3. Run this skill for a longer budget (10+ minutes) to harden the equivalence claim.
