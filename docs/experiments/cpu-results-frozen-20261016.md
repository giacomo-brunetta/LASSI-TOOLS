# Frozen C-to-Torch CPU results

Frozen on 16 October 2026. This task translates C reference kernels to Torch
and verifies execution on CPU; it is not a Torch-to-CPU compilation benchmark.

| Model (medium effort) | Verified kernels | Kernel success | Accepted candidate outcomes |
| --- | ---: | ---: | ---: |
| GPT-5.6 Luna | 32/33 | 97.0% | 92/94 (97.9%) |
| GPT-5.6 Terra | 33/33 | 100.0% | 96/98 (98.0%) |
| GPT-OSS 120B | 30/33 | 90.9% | 71/95 (74.7%) |

Across the 33-kernel MINI suite (24 PolyBench and nine scientific kernels),
Terra verified every kernel, Luna missed only Deriche, and GPT-OSS missed
Deriche, Gram--Schmidt, and wavelet compression. A kernel succeeds when at least
one candidate matches the deterministic C FP64 live-outs on CPU with
`rtol=1e-10` and `atol=1e-12`. Each campaign planned three candidates per kernel
with up to two correction rounds, at medium reasoning effort; GPT-OSS was
served through OpenRouter pinned to Groq. Candidate fractions count recorded
terminal outcomes in the selected run, not all 99 planned slots or historical
attempts. These are fixture-level FP64 translation results, not proof of
input generality, low-precision integrity, LARGE correctness, or accelerator
performance. Explicit FP64 arithmetic is valid for this task; invalidated
low-precision measurements do not by themselves invalidate CPU FP64 evidence.

## Separate policy-refresh experiment

The later five-kernel rerun (Correlation, ADI, Deriche, direct DFT, Durbin)
produced Terra 5/5, Luna 4/5, and GPT-OSS 3/5. Luna failed Deriche; GPT-OSS failed
Deriche and Durbin. In particular, GPT-OSS's original successful Durbin and its
later failed Durbin are different attempts. The table above freezes the original
full-suite campaigns, not the latest-policy replacement baseline; these reruns
are neither substituted into that table nor pooled with it. Their selection was
audit-driven, so they are not an independent full-suite comparison. No GPU stage
ran in this rerun, and no GPU or numerical-repair claims are made here.

## Frozen provenance

[The machine-readable snapshot](cpu-results-frozen-20261016.json) identifies all
99 selected full-suite kernel/model records and all 15 targeted reruns, with
SHA-256 hashes of run records and candidate sources. Full-suite selection uses
the last candidate-evaluated run per kernel within the named original campaign;
infrastructure-only attempts are not candidate outcomes. Raw artifacts stay in
the originating workspace under ignored `runs/`. This snapshot and report are
versioned; they do not relocate, edit, or restart any experiment. It is an
evidence index, not a distributable copy of the raw corpus.
