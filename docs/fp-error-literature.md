# Floating-point error literature review and skill backlog

Reviewed 2026-09-01. The local corpus is in `~/Desktop/Papers/FP arithmetics` and
`~/Desktop/Papers/FP16 ERROR`: 23 PDFs in total (19 and 4, respectively). This review separates
algorithmic compensation from elementary-function implementation and hardware architecture,
because evidence in one category does not automatically justify a technique in another.

## Corpus findings

### Directly actionable for low-precision scientific kernels

| Corpus item | Reusable result | Skill consequence |
|---|---|---|
| Higham & Mary, *Mixed Precision Algorithms in Numerical Linear Algebra* (2022) | Block FMA, FABsum, scaling/equilibration, iterative refinement, multiword and adaptive precision | Expand diagnosis and compensation beyond scalar compensated sums |
| Croci et al., *Stochastic Rounding* (2022) | Mode-1 versus mode-2 SR, stagnation, probabilistic evaluation, edge cases, and cast/operation distinction | Describe the shipped helper as explicit mode-1 casts, not global or “exact” SR |
| Micikevicius et al., *Mixed Precision Training* (2018) | FP32 master weights, loss scaling, FP32 accumulation | Keep these as training-only techniques; do not apply them blindly to inference kernels |
| Lehmann et al., lattice Boltzmann formats (2022) | Separate storage and arithmetic precision, baseline-shifted populations, custom range allocation | Add storage/operator/accumulator diagnosis and baseline/deviation representations |
| Brun et al., custom-precision math libraries | Per-call-site input-range and required-output-precision profiling | Add range/sensitivity diagnosis before precision assignment |
| Ozaki, Uchino, & Imamura, *Ozaki Scheme II* (2025 manuscript) | High-precision GEMM emulation through low-precision operand decomposition | Add an Ozaki/multiword GEMM option, guarded by matrix-engine capability and cost |

### Directly actionable for elementary functions

| Corpus family | Reusable result | Skill consequence |
|---|---|---|
| CORE-MATH; Lim & Nagarakatte; RLibm-All | Correct rounding is a format-and-rounding-mode contract, not “small average ULP” | Add a separate elementary-function audit skill |
| Aanjaneya & Nagarakatte, RLibm polynomial evaluation | Coefficients and evaluation scheme are coupled; changing Horner/Estrin/FMA after generation can break correctness | Require regeneration or renewed whole-domain validation after evaluation-order changes |
| Briggs, Lad, & Panchekha, MegaLibm; Sollya | Separate range reduction, approximation, reconstruction, working precision, and evaluation scheme | Audit each layer and prefer generated, checked artifacts over ad hoc polynomials |
| Brunetta thesis and executive summary; Vector RISC-V; Intel CR SIMD | Vector implementations need explicit ULP/domain evidence and target-specific special-case paths | Report vector/backend evidence separately from scalar accuracy claims |
| FFCC activation approximations; FMA-centric nonlinear acceleration | Application accuracy can permit aggressive approximations, but does not prove function-level error bounds | Approximation requires an explicit semantic/application contract and adversarial validation |

The two Intel correctly-rounded-vector PDFs contain the same paper in different files. The two
RLibm polynomial-evaluation PDFs are versions of the same CGO 2023 paper, and `RLibm-All.pdf`
is the technical-report version of the 2022 POPL paper in `Polynomial CR.pdf`. They are not
byte-identical, so retain the newest/reviewed version while treating each pair as one bibliographic
work. The CGRA trade-off, FMA hardware-sharing, and Highway slide deck are useful architecture
context but do not by themselves establish a source-level FP compensation method.

## Additional literature to add

These primary sources fill the largest gaps in the local folders.

| Priority | Source | Why it matters here |
|---:|---|---|
| 1 | Blanchard, Higham, & Mary, [FABsum](https://doi.org/10.1137/19M1257780) | Formal basis for low-precision block sums with accurate combination; now represented by `blocked-fp32` |
| 1 | Ogita, Rump, & Oishi, [Accurate Sum and Dot Product](https://doi.org/10.1137/030601818) | Error-free transforms and compensated dot products, the next logical primitive after compensated sums |
| 1 | Blanchard et al., [Mixed Precision Block FMA](https://doi.org/10.1137/19M1289546) | Shows why input, internal accumulator, and output precision must be recorded separately |
| 1 | Fasi et al., [Multiword Matrix Multiplication](https://doi.org/10.1137/21M1465032) | Explains tensor-core rounding hazards and how blocked summation improves multiword GEMM |
| 1 | Carson & Higham, [GMRES-based Iterative Refinement](https://doi.org/10.1137/17M1122918) | Gives conditioning and residual requirements absent from the old generic “mixed-refine” label |
| 1 | Iakymchuk et al., [ExBLAS implementation](https://github.com/riakymch/exblas) | Expansion and superaccumulator approaches for accurate, reproducible reductions |
| 2 | Rubio-González et al., [Precimonious](https://doi.org/10.1145/2503210.2503296) | Dynamic precision search under accuracy/performance constraints |
| 2 | Chiang et al., [FPTuner](https://soarlab.org/papers/2017_popl_cbbsgr.pdf) | Formal error-bounded mixed-precision assignment and cast/vectorization constraints |
| 2 | Diffenderfer, Osei-Kuffuor, & Menon, [error-bounded dot products](https://doi.org/10.1137/21M1406994) | Deterministic error budgets for approximate dot-product components |
| 2 | Fasi & Mikaitis, [CPFloat](https://doi.org/10.1145/3585515) | Reproducible simulation of formats, rounding modes, subnormals, and overflow policies |
| 3 | Kohl, McCormick, & Tamstorf, [block floating-point multigrid](https://arxiv.org/abs/2307.00124) | Progressive precision and shared-exponent scaling for structured PDE solvers |
| 3 | Hao et al., [runtime-reconfigurable precision for PDEs](https://arxiv.org/abs/2409.15073) | Runtime range profiling and dynamic precision, mainly relevant to future hardware-aware planning |

## Technique backlog

The ranking reflects fit with source-level PyTorch transformations, available validation, and likely
backend portability. “Agent-authored” means the technique is now recognized by the compensation
skill but has no generic deterministic helper.

| Rank | Technique | Failure addressed | Current status | Required evidence |
|---:|---|---|---|---|
| 1 | FP32 accumulation | Reduction swamping | Existing helper | Explicit FP32 ops and paired latency/error |
| 1 | FABsum-style blocked FP32 accumulation | Long reductions where full wide work is costly | Added helper | Block-size sweep and lowered accumulator behavior |
| 1 | Stable algebraic reformulation (`log1p`, `expm1`, max-shifted softmax, scaled norms/variance) | Cancellation, overflow, unstable composites | Added agent-authored option | FP64 oracle, domain boundaries, and target compile |
| 1 | Exact power-of-two scaling and matrix equilibration | FP16 overflow, underflow, poor range use | Scaling existing; equilibration added agent-authored | Intermediate ranges, structure preservation, correct unscaling |
| 1 | Baseline/deviation storage and zero-centering | Large offset plus small signal | Existing, with stronger guidance | Algebraic reconstruction and state-drift checks |
| 1 | Residual carry/error feedback for state updates | Repeated updates below one ULP | Added agent-authored option | Persistent-state contract and long-horizon invariant |
| 2 | Pairwise, superblock, Kahan, and Neumaier reductions | Order-dependent reduction error | Pairwise/Kahan/Neumaier existing | Compare native optimized reduction; inspect compensation precision |
| 2 | Error-free dot product (TwoProd/FMA plus accurate sum) | Cancellation in contractions | Proposed next helper | True FMA/lowering evidence and no reassociation |
| 2 | Target-format multiword arithmetic | No wider scalar arithmetic | Corrected existing double-word; broader expansion proposed | Same exponent range, strict evaluation, performance |
| 2 | Ozaki/multiword GEMM splitting | Accurate GEMM on fast low-precision matrix units | Added agent-authored option | Split count, GEMM count, accumulator rounding, target speedup |
| 2 | Precision ramp for convergent iterations | Early iterations overcomputed; late iterations inaccurate | Added agent-authored option | Residual history, stopping criterion, monotone precision policy |
| 2 | Standard or GMRES-based iterative refinement | Low-precision factorization/solve error | Existing generic option, now constrained | Conditioning, high-precision residual, convergence and failure limit |
| 2 | Per-tensor/block adaptive precision | Unequal sensitivity or magnitude across data | Added to guidance; search automation proposed | Held-out datasets or formal error bounds; cast overhead |
| 2 | Mode-1 stochastic casts | Stagnation and one-sided rounding drift | Existing helper, semantics corrected | Multiple seeds, mean/variance/quantiles, overflow/subnormal policy |
| 3 | Binned, expansion, or Kulisch/superaccumulator reduction | Bitwise reproducibility and extreme cancellation | Proposed | Backend implementation, memory cost, deterministic final rounding |
| 3 | Correctly rounded or bounded-ULP elementary functions | Backend libm disagreement or weak native functions | New audit skill; no generator | Full-domain/rounding-mode evidence or clearly bounded domain |
| 3 | Precision autotuning with formal or empirical bounds | Large search spaces | Proposed | Search budget, held-out validation, cast/vectorization constraints |
| 4 | Custom formats, posit, block floating point, runtime-reconfigurable precision | Format mismatch with application range | Research/target-specific | Actual backend support or faithful simulation plus deployment path |
| Conditional | Loss scaling, FP32 master weights, wide optimizer state | Training underflow and update loss | Deliberately training-only | A real training loop and optimizer state in scope |

## Corrections made from the audit

1. BF16 `double-word` used FP16 components. This could overflow values that are ordinary BF16;
   it now preserves the input format for both high and low words.
2. The stochastic helper and skill claimed effectively global, “exact” stochastic rounding. The
   helper actually performs mode-1 rounding only at explicit casts. Its documentation now says so,
   and finite overflow follows the ordinary cast instead of silently saturating to the largest finite
   target value.
3. The Groq worker divided near-zero relative errors by `1e-30`, while Torch used
   `max(atol, 1e-30)`. Groq now uses the same tolerance-scaled definition, so backend Pareto points
   are comparable. The historical field name `max_rel_error` is retained for artifact compatibility.
4. Compensation thresholding honored `compensation.error_metric`, but Pareto-dominance selection
   silently reverted to `Measurement.y_error` (normally maximum relative error). Both thresholding
   and dominance now use the configured metric; a missing configured metric is treated as missing
   evidence, not an acceptable point.
5. Kahan/Neumaier and error-free transforms were described too categorically. The skills now state
   their rounding, reassociation, subnormal, compensation-precision, and backend-lowering limits.
6. Correct rounding, bounded ULP, finite-domain testing, and application accuracy were conflated in
   the old single compensation workflow. The new elementary-function audit keeps them separate.

## Validation policy for future additions

Every technique must retain the original C/C++ FP64 oracle as the semantic gate, pass the FP32
collapse check, declare storage/operator/accumulator/output formats, and show paired target-backend
error and latency. Stochastic techniques additionally need a seed distribution. Function
approximations need explicit domain and special-value coverage. Iterative techniques need residual,
conditioning, convergence, and stopping evidence. No literature result should be promoted to a
portable backend claim without checking the actual lowered graph.
