# Independent accuracy holdout

**October 24 recheck:** all four eligible Luna FP16 recoveries were rerun on A100
with the unchanged frozen policy and sources: **4/4 canonical controls, 41/48
individual holdouts, 0/4 complete qualifications**. Decisions match the earlier
evaluation. GPT OSS's completed numerical inventory has no eligible recovery to
qualify. See the [completed-repairs report](experiments/completed-repairs-paper-20261024/README.md).

Status: **completed for all 20 eligible FP16 full recoveries: 4/20 qualify**,
with **195/240** holdout cases and all twenty canonical controls passing. See the
[complete-coverage run record](experiments/accuracy-holdout-20261022/fp16-complete.md).
Fourteen additional targets were evaluated, with six original frozen results reused.
The original diagnostic cohort is **completed on A100: two of eleven targets passed**.
The corrected original run uses
[freeze v2](../runs/accuracy-holdout-freeze-v2/manifest.json) and writes
[final status](../runs/accuracy-holdout-results-v2/status.json). The run covers eleven
reported recoveries (nine SOL, two Terra), with twelve holdouts and one canonical
control per target. See the [run record](experiments/accuracy-holdout-20261022/README.md).

The current repair gate, including its supplied-input perturbations, is development
evidence: agents can see its feedback. This suite supplies a separate final check
using twelve cases per recovered kernel/format/model, plus the original C fixture
as a control. It uses the declared workload dimensions, iteration counts, constants,
and printed live-outs. It makes no model calls and does not invoke input builders.

The policy is in
[accuracy_holdout.json](../experiments/holdout-validation/accuracy_holdout.json), the
harness in [holdout.py](../lassi_x/holdout.py), and harness regression checks in
[test_holdout.py](../tests/test_holdout.py). All nine harness regression tests pass;
formatting and lint checks also pass. Holdout observations are recorded separately
from the original campaign's recovery claims.

## Cases and reference

| Cases per target | Purpose |
|---|---|
| Four seeded local variations | Check nearby inputs at two perturbation magnitudes. |
| Two independent random inputs | Break initializer correlations; cover positive-offset and signed cancellation regimes. |
| Half and double scale | Check sensitivity to input magnitude. |
| Two structured fields | Exercise spatial variation beyond the original initializer. |
| Two sparse interventions | Check dependence on changes to individual input locations. |

Each independent data field gets its own random values. All implementations of a
kernel use the same seeds and canonical contract. LU and Cholesky use separate SPD
constructions: positive diagonal congruences with a diagonal shift, positive scaling,
and independently generated symmetric strictly diagonally dominant matrices. This
preserves a valid factorization problem. Those SPD cases test the listed families'
domain-preserving counterparts rather than arbitrary elementwise noise. N-body
masses remain positive, and TRMM retains its unit lower-triangular convention.
CG search direction and residual norm, low-rank residuals, and wavelet coefficients
are initialized consistently with the changed independent data.

Expected outputs come from the original C computation. The harness inserts binary
input loads immediately after initialization, retaining the computation and its
output routine. It does not translate the algorithm into Python or use a repaired
kernel as an oracle. Each original C oracle runs twice for determinism. The
configured C types are retained, including Deriche's native float arithmetic.

The harness also records a secondary C result using target-rounded input arrays
and mutable CG state. This helps diagnose input quantization. Fixed C scalar
parameters keep their original values, so this diagnostic is not a complete
lower bound on target-format error. Acceptance always uses the original,
unrounded C-input reference.

## Freeze and acceptance

After the repair campaign finishes, freeze the final recovered sources once.
`prepare` reads terminal `repair.json` records with `variant.recovered == true`,
checks the recorded source hashes, and copies both repaired and paired baseline
sources, trusted C input contracts, input schemas, C sources and build dependencies.
It also freezes and checks the six harness modules used for input binding, C
instrumentation, execution, metrics and dtype auditing.
The manifest hashes those artifacts and the policy. Existing freezes and results
cannot be overwritten. The inventory retains unsuccessful, interrupted, and
unsupported entries instead of silently counting them as passes. Existing semantic
holds are not cleared by inclusion in this inventory.

The adapters cover all seventeen kernel families in the current corrected-input
repair worklist, plus wavelet compression and IIR filter bank. Preparation supports
this campaign's artifact/schema layout; it is not a general historical-run importer.
Helpers imported from the installed harness and the Torch/compiler environment must
also be preserved with any reported experiment. Top-level candidate execution is
ordinary Python; this is not a sandbox against malicious modules.

For each case, both sources run in FP64, FP32, and the repaired target format.
The checks include finite values, complete output sizes, unchanged caller inputs,
repeatability, and observed explicit target-format tensor arithmetic. C output
boundaries define separate error components, independently of candidate packing.
In JPEG, wavelet and low-rank compression, the image, error scalar and count each
get their own relative-L2 measurement; negative error metrics or counts fail.
CUDA is configured with `CUBLAS_WORKSPACE_CONFIG=:4096:8`. Deterministic algorithms
are requested with warnings for unsupported operations; every evaluated forward
must still produce bitwise equal outputs on its two repetitions. This permits
execution of the existing CUDA cumulative sums without treating their runtime's
missing deterministic certification as a numerical failure.

A repaired kernel passes only if **every holdout and the canonical control**:

- Matches C within the existing FP64 tolerances (`rtol=1e-10`, `atol=1e-12`).
- Has worst-C-output relative L2 at most **0.01** in FP32 and the target format.
- Passes the execution, determinism, input-mutation and target-dtype checks.

Crashes, timeouts, nonfinite C outputs, unsupported layouts and other unverified
observations prevent a pass. They remain visible in the results. Paired baseline
observations show which cases were already healthy, which regress, and whether the
baseline itself satisfies the FP64 semantic check. A repair can pass the accuracy
holdout even if its baseline fails; that does not establish a fair numerical-repair
comparison against a semantically valid baseline.

Report the original recovery claim, holdout pass count, per-case errors, worst error,
baseline comparison and all failures separately. Do not redefine recovery using an
average over the cases or discard inconvenient cases. These fixed cases are a
broader differential check, not independent samples establishing a population-wide
statistical guarantee. Same-size validation does not establish other-size behavior,
implicit hardware accumulation precision, or correctness on another accelerator.

Keep the final holdout policy, cases and feedback out of agent prompts, tools and
repair retries. The files are separate from the repair pipeline; filesystem access
is not a secrecy boundary. Any subsequent tuning based on these results turns
this suite into development data and requires a new untouched final holdout.

## Run commands

The selected repair campaign finished before the holdout cohort was frozen.
The corrected run was started with the following freeze command:

```sh
.venv/bin/python -m lassi_x.holdout prepare \
  --campaign runs/input-corrected-agent-repairs-20261021 \
  --spec experiments/holdout-validation/accuracy_holdout.json \
  --output runs/accuracy-holdout-freeze-v2
```

This freezes inputs and sources without compiling C or importing candidates.
Inspect `inventory.json` and `manifest.json` before execution. The current source
hash must match its recovered measurement; drift stops preparation.

The active launcher stages the freeze and matching harness on the existing A100
endpoint, serializes targets under the campaign's shared A100 lease, and collects
progress and summaries locally:

```sh
.venv/bin/python experiments/holdout-validation/run_accuracy_holdout.py \
  --freeze runs/accuracy-holdout-freeze-v2 \
  --output runs/accuracy-holdout-results-v2 \
  --detach
```

Do not start a second launcher while the recorded PID is live. The launcher lock
also prevents duplicate local drivers. Original run v1 remains preserved; it
encountered CUDA determinism configuration errors and is not a completed numerical
qualification. Freeze v2 changes only the harness's CUDA setup and determinism
request; its sources, C references, input contracts and case policy match v1.

For manual execution, evaluate a target listed in `manifest.json` in the intended
accelerator's Torch environment:

```sh
.venv/bin/python -m lassi_x.holdout evaluate \
  --manifest runs/accuracy-holdout-freeze-v2/manifest.json \
  --target runs/accuracy-holdout-freeze-v2/sol/direct-dft/c3-bf16/target.json \
  --results /tmp/manual-holdout/sol/direct-dft/c3-bf16 \
  --device cuda \
  --timeout-s 86400
```

For manual remote submissions, use the existing host-side A100 lease in
`docs/experiments/result-validity-audit-20261020/gpu_coordination.py` around any
remote submission, and serialize targets through the shared execution agent.
This standalone command does not acquire the campaign lease or submit remote jobs.
Copy the complete freeze and matching harness installation to the evaluation host;
copied C dependencies are relocated automatically. The command spawns a child
process with a per-target deadline; a timeout kills that process group and records
an unverified result. No background evaluation is scheduled by preparation.

Each target writes the generated C source, build command/compiler version, input
archives, C outputs, candidate outputs, per-case decisions and `summary.json`.
Python, NumPy, CUDA and Torch versions, device name and manifest hash accompany the summary.
CPU execution (`--device cpu`) is useful for harness development and semantic
diagnosis; it cannot establish A100 numerical behavior.

The added regression tests can be run later with:

```sh
.venv/bin/python -m pytest tests/test_holdout.py
```

They include a tiny compiled C counterexample in which a fixture-specialized
candidate passes the original input and fails the independent holdout.
