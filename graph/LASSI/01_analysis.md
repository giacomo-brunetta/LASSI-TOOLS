# Analysis

## Kernel
- purpose: build identity matrices A(axb) and B(bxc), compute C = A*B (int GEMM), print C row-major to stdout
- entry: /Users/giacomobrunetta/Projects/LASSI-TOOLS/graph/optimized.c:56 (main)
- call path: main -> calloc A,B + diagonal write -> calloc C -> i-k-j GEMM -> per-row write_int_space + fwrite

## Build & Run
- compiler: clang
- correctness flags: -O0 -lm
- performance flags: -O3 -lm
- run: ./optimized [a b c]   (defaults a=8 b=6 c=8; argc must be 1 or 4)
- inputs: 3 positional CLI ints; benchmark args '400 400 400'; 5 runs
- golden: 8 cases; stdout must match reference (test.c) byte-for-byte

## Refactoring Targets
- optimized.c:97-110 — GEMM triple loop (i-k-j with restrict, vectorize pragma); dominant cost at 400^3 (~6.4e7 multiply-adds); candidate for blocking, OMP parallel, or exploiting identity-input structure
- optimized.c:21-54 — write_int_space integer-to-ASCII; called a*c times (1.6e5 at 400^3); minor but in hot output path
- optimized.c:83-91 — A,B allocation + diagonal init via calloc; small but redundant given identity-only inputs
- optimized.c:114-126 — per-row buffer assemble + single fwrite; already efficient, possible to batch multiple rows

## Hotspots
- Inner j-loop at optimized.c:105: int32 multiply-add, Crow/Brow contiguous streaming, Arow scalar broadcast — clang -O3 should autovectorize (NEON on arm64, AVX2/512 on x86)
- calloc zero-fill of A (a*b*4B), B (b*c*4B), C (a*c*4B): 3 sweeps of ~640KB each at 400^3
- write_int_space: integer divide-by-100 loop dominates per-element output cost
- Memory pattern: Brow stride-1, Crow stride-1, Arow scalar — cache-friendly; no obvious bottleneck below GEMM compute

## Constraints
- Must reproduce stdout byte-for-byte for 8 golden cases (args='', '2 2 2', '4 4 4', '5 3 5', '3 5 7', '400 400 400', etc.)
- Output format: each int followed by single space, then '\n' at row end (matches test.c printf "%d ")
- Edge cases: a<=0 or c<=0 -> no output; b<=0 -> a rows of c "0 " then '\n'; argc not 1 or 4 -> usage + exit 1
- Integer arithmetic only; no FP; portable C; libc/libm only

## Unknowns
- Baseline runtime of optimized.c at 400^3 not measured here (profiler phase will produce)
- Whether OpenMP / pthreads is permitted by grader (only clang + -lm specified)
- Whether clang -O3 currently emits SIMD for inner loop on host (Darwin arm64 per env)
- Whether shortcut C=A*B exploiting identity-B (or identity-A) inputs is acceptable for golden equivalence across all 8 cases (likely yes since all cases use identity init)
