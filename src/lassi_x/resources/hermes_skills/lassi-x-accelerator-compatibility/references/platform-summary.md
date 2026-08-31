# Published accelerator compatibility summary

Use this document for planning-level comparisons. Use the target wiki for any individual
operator claim.

## Evidence basis

All three snapshots use Torch-MLIR operator inventory revision
`874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`. The common comparison contains 437 included ATen
forward tensor operators: 356 have runnable canonical cases, 70 need a valid fixture, and 11 are
not applicable to the floating-point manifest cell.

| Target | Compiled / runnable | Coverage | Important qualification |
|---|---:|---:|---|
| `graphcore-pod64-poptorch` | 261 / 356 | 73.31% | FP16 common-comparison cell; PopTorch 3.3.0 |
| `alcf-cs3-cerebras-pytorch` | 234 / 356 | 65.73% | FP16, compile-only; no wafer execution |
| `groq-r01-groqflow` | 200 / 356 | 56.18% | Declared FP16 cell, but floating inputs trace as FP32 |

Only `compiled` is positive canonical compatibility evidence. It does not establish correctness,
performance, arbitrary-shape coverage, full-graph compilation, placement, or execution.

## Portable-core overlap

Of the 356 runnable cases:

| Exact compiled set | Cases |
|---|---:|
| All three targets | 154 |
| Graphcore + CS-3 only | 56 |
| Graphcore + Groq only | 19 |
| CS-3 + Groq only | 12 |
| Graphcore only | 32 |
| CS-3 only | 12 |
| Groq only | 15 |
| None | 56 |

Use the 154-case common core as a portability signal, not as a hard allow-list: exact functions
must still be queried in the wiki.

## Family-level compilation coverage

Families are a name-based planning abstraction, not compiler lowering categories. Cells show
compiled runnable canonical cases.

| Operator family | Graphcore | CS-3 | Groq |
|---|---:|---:|---:|
| Arithmetic, comparison, and logic | 55/71 (77%) | 55/71 (77%) | 53/71 (75%) |
| Transcendental math | 32/38 (84%) | 30/38 (79%) | 17/38 (45%) |
| Linear algebra | 18/27 (67%) | 14/27 (52%) | 14/27 (52%) |
| Complex, FFT, and signal | 1/3 (33%) | 1/3 (33%) | 0/3 (0%) |
| Convolution | 8/11 (73%) | 0/11 (0%) | 5/11 (45%) |
| Pooling and resampling | 6/18 (33%) | 9/18 (50%) | 5/18 (28%) |
| Activations | 24/26 (92%) | 20/26 (77%) | 21/26 (81%) |
| Normalization | 1/8 (12%) | 0/8 (0%) | 5/8 (62%) |
| Reductions and statistics | 32/40 (80%) | 29/40 (72%) | 31/40 (78%) |
| Indexing, gather, and scatter | 9/17 (53%) | 11/17 (65%) | 7/17 (41%) |
| Shape, layout, and construction | 63/76 (83%) | 57/76 (75%) | 39/76 (51%) |
| Loss functions | 7/8 (88%) | 6/8 (75%) | 3/8 (38%) |
| Random and sampling | 5/7 (71%) | 2/7 (29%) | 0/7 (0%) |
| Quantization | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) |

Planning implications:

- Arithmetic, activations, and reductions are the strongest shared families.
- Graphcore has the broadest canonical coverage overall and is strongest here for transcendental,
  convolution, shape/layout, loss, and random families.
- CS-3 is comparatively strong for indexing and pooling, but none of the tested runnable
  convolution or normalization canonical cases compiled in this snapshot.
- Groq is comparatively strong for activations, reductions, and normalization; transcendental,
  shape/layout, indexing, loss, random, and complex/signal coverage is narrower.
- Quantization is a known planning hazard on all three snapshots.

These statements describe tested canonical cases only. A zero cell is not proof that every
possible formulation in that family is unsupported.

## Exact operator authority

The detailed records remain in:

- `compat_tool/wiki/graphcore-pod64-poptorch/`
- `compat_tool/wiki/alcf-cs3-cerebras-pytorch/`
- `compat_tool/wiki/groq-r01-groqflow/`

Use `lassi-x-compat-wiki op ... --markdown` to read one page through the installed package. The
machine-readable snapshots under `compat_tool/snapshots/` are the source for bulk analysis.
