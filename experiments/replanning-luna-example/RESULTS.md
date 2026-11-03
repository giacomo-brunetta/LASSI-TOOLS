# Luna pool-level replanning example: development result

This is a completed **development smoke test** under [PLAN-v2.md](PLAN-v2.md).
The 0.1% relative-L2 threshold was chosen after observing that every candidate
passed the original 1% gate. The original observations are preserved as
`runs/replanning-luna-correlation-mini-20261102/baseline-1pct.json`; this result
is not an independent threshold comparison or a final holdout.

## Recorded commands and continuation

These are the commands used from the repository root in the locked environment.
The first two contact Luna and must not be rerun into this completed output root;
they are recorded for provenance. The third re-evaluates saved implementations
without contacting Luna. Each stage has finite session and execution budgets
in the plan.

```sh
uv run --locked --extra dev --extra globus --extra roofline lassi-x run \
  experiments/replanning-luna-example/stage1.yaml --until cpu-verified

uv run --locked --extra dev --extra globus --extra roofline python \
  experiments/replanning-luna-example/run.py \
  --stage1-run /Users/giacomobrunetta/Projects/LASSI-TOOLS/runs/replanning-luna-correlation-mini-20261102/stage1/20261103T014735.399830Z-polybench-correlation-mini-luna-replanning \
  --device mps

# Only re-evaluate the exact saved Stage 3 implementations; no Luna calls:
uv run --locked --extra dev --extra globus --extra roofline python \
  experiments/replanning-luna-example/run.py --revalidate-stage3 --device mps
```

The Stage 1 command creates a new run directory on each invocation; the second
command used the **exact directory emitted** by the recorded invocation. Do not
select a run by its modification time. A new attempt needs a distinct output root
and a separately recorded plan; the example adapter currently fixes its artifact
root for this one completed attempt.

## Observed outcomes

| Gate | Planned/executed | Result |
| --- | ---: | --- |
| Stage 1 FP64 | 3/3 | `c1`, `c2`, and `c3` passed C-oracle semantics and input checks |
| FP32/FP16/BF16 baseline | 9/9 | 6 passed 0.1% relative L2; all 3 BF16 cells had finite error above the threshold |
| Stage 2A LP planner | 1/1 call, at most 2 plans | Luna returned `[]`; no LP coder ran |
| Stage 2B MP planner/coders | 1/1 call, 2/2 plans | Both generated sources had wider ATen operations beyond the planner's declared list; both were rejected before numerical acceptance |
| Stage 3 planner/coders | 1/1 call, 2/2 plans | Chose distinct original FP16 sources, `c1` and `c2` |
| Original Stage 3 target check | 2/2 plans | Both blocked by a trusted checker error: FP64 conversion on MPS before transfer to CPU |
| Source-identical Stage 3 revalidation | 2/2 plans | Both TorchScript graphs executed on MPS, passed input parity and relative L2 = 0.0005498, and passed a source-bound MPS eager audit with no observed wider tensor operations |

The checker was fixed to transfer outputs to CPU before FP64 comparison. Original
failure records remain in `stage3-plans.json`; the corrected, source-hash-verified
checks are separate in `stage3-revalidated-v2.json`. The revalidation made **zero
model calls**. Each plan received one coder and one compiler-feedback repair
session in the original run; those feedback sessions were consumed by the checker
bug and are retained as infrastructure history, not scientific repair failures.

The revalidated host-synchronized MPS TorchScript medians were about 0.46 and
0.79 ms over three calls. These are smoke-test timings with visible variation,
not architectural device latency or a performance comparison.

## Provenance and claim limits

- C reference SHA-256: `f35de426846bd8ee6ebb77d4c96176b3cf1dbeafd4efe2d19d06f74043ce5d24`.
  C-oracle output SHA-256: `f593727e2e00909d35b00cd1a4b69acb47245c4e1f995434ca1c3c0e878537da`.
  Input-contract SHA-256: `df51698b1e3a32460d7373e8ae47c7207fd8a4e6ec7c1504f2f1180c024dc90a`.
- Stage 1 source hashes: `c1` `24941cbfb137c91ceed30ab0be4fd45b51adc218074f723cbbfc015d7424d9dd`;
  `c2` `3b914313f2bad4394d026c80874629b35c536082ed3e2c5fbe9277421c2cd26f`;
  `c3` `a7db7cd76566953dade430c69ae1ca73cf9b1f004b5fab87a07c47edd21a3128`.
- Requested model: `openai-codex/gpt-5.6-luna`. A direct Hermes preflight
  completed; the generic HTTP model doctor cannot probe this OAuth provider
  without a separate base URL. The response did not provide a resolved model ID.
  Four Stage 1 sessions, nine replanning sessions, and one preflight session were
  used, within the 16-session limit. Replanning usage was 94,957 input and 9,999
  output tokens; the provider reported no usable cost estimate.
- The MPS audit observes one eager forward's explicit ATen tensor dtypes. It does
  not certify TorchScript lowering or implicit hardware accumulation. No compiled
  precision certificate or final holdout was produced.

The evidence files are under
`runs/replanning-luna-correlation-mini-20261102/`, including `baseline.json`,
`replanning/stage2-plans.json`, `replanning/stage3-plans.json`,
`replanning/stage3-revalidated-v2.json`, and `summary-v2.json`. All planned
candidate slots and failed attempts are retained.
