# Changes

## Strategy applied
- Strategy 1 (Cache-blocked i-k-j GEMM) — wrapped main multiply in jj/kk tiles (JB=128, KB=64), i-k-j order with hoisted `int * __restrict__ Crow` / `const int * __restrict__ Brow`, `#pragma clang loop vectorize(enable) interleave(enable)` on the innermost j-loop, and an `aik==0` fast-skip (identity init makes most aik zero, so this is a large speedup with no behavior change).
- Strategy 2 (Batched output buffer) — single malloc'd buffer sized to ~1 MiB / row_cap rows (clamped to a, min 1 row); rows emitted with `write_int_space` using a 200-byte 2-digit table; one `fwrite` per batch with a final flush.
- Strategy 3 (identity skip) — NOT applied (plan flagged as high-risk / requires verifier endorsement).

## Files changed
- /Users/giacomobrunetta/Projects/LASSI-TOOLS/graph/optimized.c: replaced VLA A/B/C with calloc'd flat arrays (so 400^3 sizes are safe); added tiled GEMM; added `write_int_space` + batched output. Preserved seed defaults (a=8,b=6,c=8) and argc-not-in-{1,4} usage/exit-1. Added explicit short-circuits for `a<=0`/`c<=0` (no output) and `b<=0` (a rows of c "0 " then '\n') to match the plan's behavior contract without relying on VLA UB.

## Build check
- command: clang -O3 -lm optimized.c (perf); clang -O0 -lm optimized.c (correctness)
- result: ok (both builds clean, no warnings)

## Smoke check
- inputs: '', '2 2 2', '4 4 4', '5 3 5', '3 5 7', '400 400 400', argc=2 (`1 2`), argc=5 (`a b c d`)
- result: matches reference byte-for-byte on all 8 cases at both -O0 and -O3 (usage line differs only in argv[0] path, expected); informal wall-time at 400^3: reference ~0.02-0.03s, optimized <0.01s.

## Behavior change
- none for the documented contract. Heap allocation replaces VLAs, so large 400^3 inputs are robust where the reference VLA would risk stack overflow; OOM path now returns 1 instead of crashing.

## Unresolved risks
- `write_int_space` assumes int fits in 11 chars + sign + space (cell_cap=12) — safe for 32-bit int; verifier should be aware before any int64 widening.
- Output buffer sized from `c * 12 + 1`; the 400^3 case stays well within the 1 MiB batch target. Very large c would shrink batch_rows toward 1 (degrades gracefully to per-row fwrite, identical to baseline behavior).
- Negative/zero-dim edge cases (a<=0, c<=0, b<=0) are handled via explicit short-circuits per the plan's contract; the 8 listed goldens do not directly exercise them, so verifier should confirm if such cases appear in the wider test set.
- `aik==0` skip is correctness-preserving (skipping a zero multiply-add) but accelerates the identity-init case dramatically; gives identical results for arbitrary inputs.
- Plan referenced line numbers from a previously-optimized baseline; the seeded target was the naive reference. Implemented the plan's intent against the naive baseline.
