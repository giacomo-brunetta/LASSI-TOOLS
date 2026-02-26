# Phase 3 Refactor Plan — EELS TensorFlow Optimization

## Inputs

- Analysis: `LASSI/phase1_analysis.md`
- Baseline: `LASSI/phase2_baseline.md`
- Baseline latency anchor: **0.68054 ms/inference** (midpoint of run means, with observed run-to-run noise)
- Mandatory runtime environment: containerized execution only

Canonical execution template (must be used for all validation and benchmarking commands):

```bash
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "<COMMAND>"
```

## Goals and Hard Gates

1. Preserve functional behavior relative to baseline outputs.
2. Improve latency vs baseline under apples-to-apples methodology.
3. Keep changes non-destructive and reversible per technique.
4. Produce verification evidence for each candidate before progressing.

Global go/no-go gates:

- **Correctness gate (mandatory):** candidate must pass output equivalence policy for its precision class.
- **Performance gate:** candidate must beat baseline anchor and baseline rerun distribution under same protocol.
- **Reproducibility gate:** all measurements must use same seeds, shapes, warmup, and measured iteration counts.

---

## Prioritized Optimization Backlog (Impact × Risk)

### P0 — Graph-level inference cleanup/fusion (first to implement)

Scope:

- Freeze inference path and ensure dropout is inactive in serving path.
- Eliminate redundant identity/reshape/transpose chains when legal.
- Enable optimizer passes that improve conv + activation scheduling/fusion opportunities.

Expected impact:

- **Latency:** 5–15% improvement.
- **Energy:** low-to-moderate reduction expected (proxy via runtime reduction, since direct RAPL was unavailable).

Risk:

- **Low to Medium** (semantic-preserving graph rewrites can still alter accumulation order).

Acceptance criteria:

- Equivalence target: strict FP tolerance (`rtol=1e-6`, `atol=1e-6`) on selected authoritative output.
- Latency target: at least **8% mean reduction** vs 0.68054 ms anchor and improved median across repeats.

Fallback if fails:

- Disable newest rewrite pass incrementally, bisect transformation stack, keep only proven-safe passes.

---

### P1 — Mixed precision inference (FP16/BF16 variants)

Scope:

- Evaluate FP16 and BF16 execution paths where backend/runtime supports it.
- Keep same graph topology and I/O interface.

Expected impact:

- **Latency:** 10–30% (hardware dependent).
- **Energy:** moderate reduction expected when reduced-precision execution is accelerated.

Risk:

- **Medium** (numeric drift in latent outputs; hardware dependence for realized speedup).

Acceptance criteria:

- Equivalence target: relaxed tolerance for mixed precision (`rtol=5e-3`, `atol=5e-4`), plus per-dimension max abs error report.
- Stability target: no NaN/Inf in outputs.
- Latency target: at least **10% mean reduction** and lower or equal p95 vs baseline rerun.

Fallback if fails:

- Try BF16 when FP16 fails numerically.
- Keep precision mixed only on conv blocks; restore dense heads to FP32 if drift is concentrated there.
- Revert to P0 candidate if no precision variant satisfies both correctness and performance gates.

---

### P2 — PTQ dynamic range quantization (int8 weights, dynamic activations)

Scope:

- Apply dynamic PTQ variant first (lower integration complexity).
- Use representative EELS-like calibration/evaluation set for sanity and thresholding.

Expected impact:

- **Latency:** 10–25% (backend dependent).
- **Energy:** moderate reduction expected from int8 arithmetic/memory footprint.

Risk:

- **Medium to High** (activation scale mismatch can degrade latent fidelity).

Acceptance criteria:

- Equivalence target: `rtol=1e-2`, `atol=2e-3`.
- Sensitivity target: distinct inputs must produce distinct outputs (non-constantized behavior).
- Latency target: at least **12% mean reduction** vs baseline anchor.

Fallback if fails:

- Tighten calibration data representativeness and retry once.
- If still failing correctness gate, discard dynamic PTQ and move to full-int8 PTQ only if expected gain justifies risk.

---

### P3 — PTQ full integer quantization (int8 weights + int8 activations)

Scope:

- Full integer path with representative dataset calibration.
- Preserve I/O contract at external interface (dequantized comparison in verifier).

Expected impact:

- **Latency:** 15–35% potential.
- **Energy:** high reduction potential.

Risk:

- **High** (largest numeric drift risk).

Acceptance criteria:

- Equivalence target: `rtol=2e-2`, `atol=5e-3`, with error histogram summary and worst-case sample capture.
- Latency target: at least **15% mean reduction**.
- Regression guard: no sample exceeds absolute error cap of 0.05 on authoritative output tensor.

Fallback if fails:

- Recalibrate once with stratified representative inputs.
- If still failing, reject full-int8 PTQ and keep best passing candidate from P0/P1/P2.

---

### P4 — QAT contingency (only if PTQ cannot pass equivalence)

Scope:

- Use quantization-aware training to recover fidelity lost in PTQ.
- Keep architecture unchanged; limit to quantization simulation and fine-tune process.

Expected impact:

- **Latency/Energy:** similar deployment gains to successful int8 PTQ.
- **Accuracy/equivalence:** improved likelihood versus PTQ-only.

Risk:

- **Very High** (requires training workflow/data/time; larger project scope).

Acceptance criteria:

- Equivalence target: match or outperform PTQ thresholds (`rtol<=1e-2`, `atol<=2e-3`).
- Latency target: must still meet at least **12% mean reduction**.

Fallback if fails:

- Stop QAT branch; retain best validated non-QAT candidate.
- Escalate for re-planning if no candidate meets mandatory correctness + performance gates.

---

### P5 — Optional pruning/sparsity (conditional)

Scope:

- Evaluate structured pruning (channel/filter-level) only if backend can exploit sparsity.
- Avoid unstructured pruning unless sparse kernels are confirmed beneficial.

Expected impact:

- **Latency:** 0–20% (highly backend dependent).
- **Energy:** potentially favorable if sparse kernels/materialization are efficient.

Risk:

- **High** (benefit uncertain, fidelity risk, often needs retraining).

Acceptance criteria:

- Equivalence target: same as precision path used (FP32/mixed/int8 class).
- Latency target: must beat best previously accepted candidate by at least **3%** to justify added complexity.

Fallback if fails:

- Drop sparsity path immediately; do not block mainline optimization rollout.

---

## Apples-to-Apples Benchmarking Protocol (Exact)

All runs (baseline replay + each candidate) must use:

1. Same container template and working directory.
2. Same deterministic seeds:
   - NumPy seed: `1234`
   - TensorFlow seed: `1234`
3. Same fixed input tensor properties:
   - shape `(1, 240, 1)`
   - dtype `float32`
   - identical generated tensor persisted and reused across baseline/candidate comparisons.
4. Same timing protocol:
   - warmup: 10
   - measured iterations per repeat: 50
   - repeats: 7
5. Same output extraction path and authoritative output selection policy.

Required measurements per run:

- mean / median / min / max / stdev / CV / p95 latency.
- run metadata (commit hash/variant tag, precision mode, quantization config).
- warning/log triage (deprecations, unsupported ops, fallback behavior).

Comparison policy:

- Use baseline anchor 0.68054 ms as first filter.
- Also rerun current baseline once before final decision to account for noise; candidate must outperform both:
  - anchor-based threshold, and
  - fresh baseline median (same session/protocol).

Decision rule for “performance win”:

- Candidate passes if:
  - mandatory correctness gate passes, and
  - mean latency improves by required per-technique threshold, and
  - median improves (or ties within 1%) with no p95 regression > 5%.

---

## Functional Equivalence and Numeric Policy

Authoritative-output rule:

- Pin one authoritative inference output tensor for all phase-4/5 checks (consistent with current serving/export path used in baseline).

Verification tiers:

1. **Tier A (FP32-preserving transformations):**
   - `rtol=1e-6`, `atol=1e-6`
2. **Tier B (mixed precision FP16/BF16):**
   - `rtol=5e-3`, `atol=5e-4`
3. **Tier C (int8 PTQ/QAT):**
   - dynamic PTQ: `rtol=1e-2`, `atol=2e-3`
   - full-int8 PTQ: `rtol=2e-2`, `atol=5e-3`

Common mandatory checks:

- deterministic repeatability check (same input, same output within tolerance class),
- input-sensitivity check (at least two distinct inputs produce distinguishable outputs),
- NaN/Inf check,
- diff/tolerance report archived under `LASSI/`.

---

## Execution Sequence (Implementation Handoff)

1. Reproduce baseline once with exact protocol (noise re-anchor).
2. Implement and evaluate P0.
3. If P0 passes, treat as reference optimized baseline.
4. Evaluate P1 variants (BF16/FP16) against best passing candidate.
5. Evaluate P2, then P3 only if justified.
6. Trigger P4 (QAT) only when PTQ fails equivalence but quantization gains remain strategic.
7. Evaluate P5 only if backend sparse benefit is demonstrated.

Stop condition:

- Select best candidate that satisfies mandatory correctness gate and highest stable latency gain under protocol.

---

## Recovery / Fallback Loops

### If correctness fails

1. Re-run once to rule out non-determinism.
2. If still failing:
   - isolate offending optimization knob,
   - revert to last passing candidate,
   - record first concrete mismatch and reproduction command.

### If performance fails to beat baseline

1. Confirm apples-to-apples settings (seeds/input/warmup/iterations/container).
2. Re-run once.
3. If still not improved:
   - reject candidate,
   - continue to next prioritized technique,
   - if all candidates fail, return to planning with measured blocker evidence.

### If results are noisy/inconclusive

1. Keep same settings; increase repeats from 7 to 11 (single exception policy).
2. Decide by median + p95 trend with unchanged protocol.

---

## Expected Outcome Targets (Phase-level)

- **Primary target:** achieve a validated candidate with **>=12% mean latency reduction** versus 0.68054 ms anchor, while passing equivalence policy.
- **Stretch target:** **>=20% mean latency reduction** with acceptable numeric drift for non-FP32 modes.
- **Non-negotiable:** no promotion of any candidate that fails functional equivalence gate for its declared precision class.

---

## Replanning Addendum — Quantization Recovery (Post Phase-5 Retry)

### A) Failure Evidence Synthesis (from latest verification)

Evidence sources:

- `LASSI/verification_report.md`
- `LASSI/verification_results.json`

Observed verified state:

- Passing: `fp32_baseline_savedmodel` (`IDENTICAL`), `graph_xla_savedmodel` (`IDENTICAL`), `mixed_fp16_savedmodel` (`ACCEPTABLE_NUMERIC_DRIFT`), `mixed_bf16_savedmodel` (`ACCEPTABLE_NUMERIC_DRIFT`).
- Failing: `ptq_dynamic_int8` (`DIFF_EXISTS`), `ptq_full_int8` (`DIFF_EXISTS`).

Error pattern:

- `ptq_dynamic_int8` fails both heads (`z_mean`, `z_log_var`) with max abs error slightly above tolerance caps (`~2.85e-3`, `~3.07e-3` vs `atol=2e-3`).
- `ptq_full_int8` fails primarily on `z_log_var` (`max_abs_error ~5.84e-3` vs `atol=5e-3`), while `z_mean` remained within tolerance.
- Input sensitivity remains true for all variants, so this is quantization error (scale/zero-point/calibration coverage), not constantization.

Root-cause hypothesis (planning assumption):

1. Calibration set under-represents activation distribution tails impacting variance head (`z_log_var`).
2. Uniform quantization policy across graph likely over-quantizes sensitive late-stage/statistical heads.
3. Output tensor quantization granularity likely too coarse for low-magnitude log-variance regions.

### B) Revised Low-Risk Quantization Candidate Set (ordered)

#### Q1 — Float16 TFLite quantization (preferred first quantized recovery path)

- Convert to float16-weights TFLite (float32 I/O retained where feasible).
- Goal: recover most quantization speed/memory gain with materially lower drift risk than int8.
- Why first: current mixed FP16/BF16 SavedModel already passes drift policy, indicating precision reduction is viable when quantization noise is controlled.

#### Q2 — Dynamic-range int8 with improved representative coverage + selective exclusions

- Expand representative dataset to cover amplitude/temporal extremes and edge patterns seen in EELS inputs.
- Apply selective quantization: keep sensitive tail/head ops in float (especially path feeding `z_log_var`) if tooling permits.
- Prefer per-channel weight quantization where supported for conv/dense kernels.

#### Q3 — Full-int8 with selective fallback (only if Q2 misses performance target)

- Keep int8 in robust backbone blocks.
- Force float fallback for final projection/head layers or dequantize earlier near output heads.
- Enable per-channel for weights and calibrated activation ranges from expanded dataset.

#### Q4 — Non-quantized winner policy (safety net)

- If all quantized candidates fail equivalence gates, final winner is selected from already passing non-quantized set (`graph_xla_savedmodel`, `mixed_fp16_savedmodel`, `mixed_bf16_savedmodel`) based on apples-to-apples performance.

### C) Explicit Equivalence Acceptance Criteria (per output head)

Pinned output order remains mandatory: `z_mean`, `z_log_var`.

For a candidate to pass, **both heads** must satisfy all criteria:

1. **Per-head tolerance gate**
   - Float16 TFLite candidate: `rtol=5e-3`, `atol=5e-4` for `z_mean` and `z_log_var`.
   - Dynamic int8 candidate: `rtol=1e-2`, `atol=2e-3` for each head.
   - Full-int8 candidate: `rtol=2e-2`, `atol=5e-3` for each head.
2. **Per-head worst-case cap**
   - `z_mean`: max abs error must remain <= class `atol`.
   - `z_log_var`: stricter guard for sensitivity: max abs error <= min(class `atol`, 5e-3).
3. **Behavioral integrity**
   - input-sensitivity true on both heads (distinct inputs -> distinct outputs).
   - no NaN/Inf.

Classification policy remains:

- `IDENTICAL` or `ACCEPTABLE_NUMERIC_DRIFT` => pass.
- `DIFF_EXISTS` => fail and route to fallback branch.

### D) Quantization Recovery Decision Tree

1. Run Q1 (float16 TFLite).
   - If equivalence pass + measurable speedup: keep as provisional quantized winner.
   - Else -> Q2.
2. Run Q2 (dynamic int8 + improved calibration + selective exclusions).
   - If pass + speedup >= target: keep.
   - If fails equivalence: tune representative set once and retry once.
   - If still fail -> Q3.
3. Run Q3 (full int8 selective fallback).
   - If pass + speedup >= target: keep.
   - If fail -> declare quantization branch unsuccessful for this cycle.
4. If quantization branch unsuccessful, pick best non-quantized passing candidate (Q4 policy) for final performance claim.

Retry budget:

- Maximum one remediation retry per quantization technique before escalation/fallback.

### E) Final Apples-to-Apples Profiling Protocol (verification-passing candidates only)

Only profile candidates with Phase-5 pass status (`IDENTICAL` or `ACCEPTABLE_NUMERIC_DRIFT`).

Mandatory command form:

```bash
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "<COMMAND>"
```

Protocol lock:

1. Same fixed seed set (`1234` for Python/NumPy/TF/PYTHONHASHSEED).
2. Same persisted input tensors and shape `(1, 240, 1)` dtype `float32`.
3. Same warmup/measurement schedule: warmup `10`, iterations `50`, repeats `7`.
4. Same host/container runtime and thread settings.
5. Same output pinning and post-processing path.

Candidate pool for final profiling round:

- Mandatory: `fp32_baseline_savedmodel` (fresh rerun baseline), `graph_xla_savedmodel`, `mixed_fp16_savedmodel`, `mixed_bf16_savedmodel`.
- Conditional: any newly remediated quantized candidate that passes equivalence.

Winning rule:

1. Candidate must pass equivalence gate.
2. Candidate mean latency must beat both:
   - baseline anchor (`0.68054 ms`), and
   - fresh baseline median from same profiling session.
3. Candidate p95 must not regress >5% vs fresh baseline.
4. If multiple pass, choose highest stable mean reduction; tie-breaker is lower p95 then lower stdev/CV.

Final fallback winner-selection policy:

- If no quantized candidate passes equivalence + performance, final claim uses best non-quantized passing winner.
- Quantization is reported as "attempted but not accepted" with first concrete mismatch evidence retained in verification artifacts.
