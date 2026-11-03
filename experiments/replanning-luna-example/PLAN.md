# Luna pool-level replanning example

## Question and scope

- Experiment ID: `replanning-luna-correlation-mini-20261102`.
- Question: can one Luna planner view all three formulations and propose distinct
  same-precision numerical repairs, then selective mixed-precision repairs, and
  choose portable specializations from the validated family?
- Unit: one PolyBench correlation kernel, three Stage 1 candidate slots (`c1`–`c3`),
  each evaluated at FP64, FP32, FP16, and BF16 on the MINI workload. Stage 3 is one
  local MPS target, if its requested precision and graph are supported.
- Interface: explicit example adapter around `lassi_x.replanning.ReplanningRun`.
  This does not change the historical `lassi-x run` stages.
- Output root: `runs/replanning-luna-correlation-mini-20261102/`. This is a development
  demonstration, not a final holdout or a paper result.

## Frozen inputs and environment

| Input | SHA-256 |
| --- | --- |
| `benchmarks/polybench/datamining/correlation/correlation.c` | `f35de426846bd8ee6ebb77d4c96176b3cf1dbeafd4efe2d19d06f74043ce5d24` |
| `benchmarks/polybench/datamining/correlation/correlation.h` | `a01fbab134e2b8fcd9591f5349551dadc8f8c9814d6be03901d1977c156cca6f` |
| `benchmarks/polybench/utilities/polybench.c` | `5de1de319495831bdb589a1ae8c2bfaf336f55c5549ab428c83d9d5905177f58` |
| `benchmarks/polybench/utilities/polybench.h` | `a709a71b20ae86e46215c2645c604ea0296771bc3e8efbce63bcd9676f58b521` |
| `uv.lock` | `bcd3d348be7393d537ac1dfa7c8a57e1c41f2de9216bdab1246d47fc30c23715` |

Harness commit: `220ab034be5dfaf7b0885daf30a8af8e4794b801` plus the
uncommitted example adapter. Python 3.12.13, uv 0.11.7, Torch 2.13.0.
Mac MPS is available; CUDA is not. Model configuration is
`provider: openai-codex`, `model: gpt-5.6-luna`, `reasoning_effort: medium`.
Credential values are never copied into artifacts. The endpoint identity and
resolved model must be recorded by preflight before scored calls.

## Gates and budgets

| Stage | Gate | Budget |
| --- | --- | --- |
| Oracle | C99 `-O0`, no FP contraction, `MINI_DATASET`, double, 17-digit output; two identical runs | one build, two runs, 120 s each |
| Stage 1 | C oracle FP64, input parity, `rtol=1e-10`, `atol=1e-12` | one planner call, three coder calls, zero correction rounds |
| Baseline | FP32/FP16/BF16 results for all three slots, including errors and blockers | nine CPU cells, 120 s each |
| Stage 2A | original precision, no explicit wider tensor arithmetic, accuracy `relative_l2 <= 0.01` | one planner call, up to two plans, one coder call per plan |
| Stage 2B | named selective promotions, no full FP32 fallback, same accuracy gate | one planner call, up to two plans, one coder call per plan |
| Stage 3 | MPS graph compile/execution and accuracy, with no new promotions; benchmark only valid implementations | one planner call, up to two plans, one coder call per plan, at most one compiler-feedback repair per plan |

At most 16 Luna sessions including one model preflight and two optional backend
repair sessions. Each session has at most 12 model iterations; each turn has a
300 s timeout, no transport retry, and at most 8192 output tokens. Numerical and target
commands have 120 s timeouts. Run one model session and one device task at a time.
Stop on an unknown model identity, missing credential, source/input hash mismatch,
or unverified precision audit. Preserve every failed and incomplete slot.

## Artifacts and reporting

- `stage1/`: config, oracle, candidate source and CPU validation records.
- `stage2-plans.json`: full plan, code, outcomes, and promotion evidence.
- `stage3-plans.json`: selected source, backend profile, implementation,
  compile/repair/accuracy/timing evidence.
- `summary.json`: all planned slots and terminal/incomplete classifications.
- Final holdout: outside this development example.

An LP tag alone is not a precision certificate. A source-bound executed audit can
support only a claim about observed explicit tensor arithmetic. Compiler lowering
and implicit accumulator precision remain outside this example's evidence.
