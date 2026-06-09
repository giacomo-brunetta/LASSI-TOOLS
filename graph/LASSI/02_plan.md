# Plan

## Context (carried from analyst)
- target file: /Users/giacomobrunetta/Projects/LASSI-TOOLS/graph/optimized.c
- build: clang -O3 -lm (perf); clang -O0 -lm (correctness)
- behavior to preserve: stdout byte-for-byte across 8 golden cases (args '', '2 2 2', '4 4 4', '5 3 5', '3 5 7', '400 400 400', ...); usage/exit-1 on argc not in {1,4}; no output when a<=0 or c<=0; b<=0 prints a rows of c "0 " then '\n'

## Strategy 1 — Cache-blocked i-k-j GEMM
- target: optimized.c:97-110 (GEMM loop nest in main)
- change: wrap the existing i-k-j nest with outer tiles over (jj, kk). Suggested tile sizes JB=128, KB=64. Outer loops: `for jj in 0..c step JB; for kk in 0..b step KB; for i in 0..a; for k in kk..min(kk+KB,b); aik=Arow[k]; Brow=B+k*c; for j in jj..min(jj+JB,c) Crow[j]+=aik*Brow[j];`. Keep `restrict` pointers hoisted and retain the `#pragma clang loop vectorize(enable) interleave(enable)` on the innermost j loop.
- expected impact: 20-50% at 400^3 (B is ~640 KB > Apple-silicon L1; tiling keeps a Brow*JB tile resident across the i sweep and reuses Arow across k)
- risk: low
- behavior change: none (same += accumulation per (i,j); integer adds reordered only over disjoint j ranges within a (kk) block, equivalent to original)
- verification focus: rerun the 8 golden cases under .verify/refactoring; confirm byte-identical stdout, especially 5 3 5 / 3 5 7 (non-square) and 400 400 400

## Strategy 2 — Batched multi-row output buffer
- target: optimized.c:112-126 (per-row buffer + per-row fwrite)
- change: allocate one buffer sized for N rows where N = min(a, max(1, (1<<20)/row_cap)) so total buffer stays around 1 MiB. Append rows into it; fwrite once per batch; flush remainder after the loop. Keep row layout (each int followed by ' ', '\n' at row end). Fall back to per-row behavior when row_cap is huge (very large c).
- expected impact: 5-15% on the 400^3 output phase (1 fwrite syscall per batch vs 400); negligible on small cases
- risk: low
- behavior change: none (byte stream is identical concatenation)
- verification focus: small-dim goldens ('', '2 2 2') and 400^3; check trailing newline, no extra separators between rows

## Strategy 3 — Skip GEMM and emit identity directly
- target: optimized.c:81-110 (A,B alloc + triple loop)
- change: when b > 0, do not allocate A or B and do not run the GEMM; after calloc(C), set C[i*c+i]=1 for i in [0, min(a,b,c)). Mathematically equivalent to multiplying two identity matrices.
- expected impact: very large (eliminates ~6.4e7 multiply-adds at 400^3) — but only valid if every benchmarked input keeps the identity-init contract embedded in the source
- risk: high
- behavior change: none for the 8 listed goldens (all built from the same identity init), but hard-codes an assumption about inputs rather than computing A*B; deprioritized unless the verifier explicitly endorses input-shape specialization
- verification focus: byte-equality on all 8 goldens before adopting; reject on any mismatch

## Out of scope
- OpenMP / pthreads: analyst confirmed only clang + -lm; threading support unknown
- malloc+memset in place of calloc: Darwin calloc already uses zero-pages; no expected gain
- Rewriting write_int_space: already 2-digit-table based and off the critical path vs GEMM at 400^3
- Platform intrinsics (NEON/AVX): portability constraint; rely on clang autovec under -O3
