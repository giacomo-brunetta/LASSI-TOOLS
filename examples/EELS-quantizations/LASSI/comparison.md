# Phase 6 Post-Optimization Profiling — EELS TensorFlow

## Scope and Equivalence Gate

- Phase 6 re-profiling only.
- Canonical container launcher used for all runs:
  - `docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "<COMMAND>"`
- Same methodology as baseline:
  - Seed: `1234` (Python/NumPy/TensorFlow)
  - Input: shape `(1, 240, 1)`, dtype `float32`
  - Warmup `10`, iterations `50`, repeats `7`
- Primary winner eligibility is restricted to **IDENTICAL** candidates from verification:
  - Eligible: `fp32_baseline_savedmodel`, `graph_xla_savedmodel`
  - Not eligible for strict-equivalence winner selection: all `ACCEPTABLE_NUMERIC_DRIFT` variants
  - Excluded as invalid: `DIFF_EXISTS` variants (`ptq_dynamic_int8`, `ptq_full_int8`)

## Metric Source

- Raw metrics artifact: `LASSI/phase6_metrics.json`
- Verification classifications source: `LASSI/verification_report.md`

## Primary (Strict-Equivalence) Comparison

All values are per-inference latency in milliseconds.

| Variant | Equivalence | mean | median | p95 | std | CV % | Δ mean vs baseline (ms) | Improvement vs baseline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_original | Baseline | 0.637590 | 0.599009 | 0.773755 | 0.079776 | 12.512 | 0.000000 | 0.000% |
| fp32_baseline_savedmodel | IDENTICAL | 0.641609 | 0.619107 | 0.766517 | 0.075507 | 11.768 | +0.004020 | -0.630% |
| graph_xla_savedmodel | IDENTICAL | 0.331959 | 0.330441 | 0.338665 | 0.004455 | 1.342 | -0.305631 | +47.935% |

## Secondary (Non-Primary) Results — ACCEPTABLE_NUMERIC_DRIFT

Reported for reference only; not valid as strict winner under user requirement.

| Variant | Equivalence | mean | median | p95 | std | CV % | Improvement vs baseline |
|---|---:|---:|---:|---:|---:|---:|---:|
| mixed_fp16_savedmodel | ACCEPTABLE_NUMERIC_DRIFT | 0.656578 | 0.627559 | 0.769098 | 0.066017 | 10.055 | -2.978% |
| mixed_bf16_savedmodel | ACCEPTABLE_NUMERIC_DRIFT | 0.661207 | 0.624751 | 0.774300 | 0.065548 | 9.913 | -3.704% |
| ptq_float16_tflite | ACCEPTABLE_NUMERIC_DRIFT | 0.015347 | 0.014453 | 0.018329 | 0.001713 | 11.161 | +97.593% |

## Energy

- Direct energy counters remain unavailable in this container context (no readable RAPL `energy_uj`), consistent with Phase 2 constraints.
- Decision is based on latency comparison under apples-to-apples protocol.

## Decision

**OPTIMIZATION_SUCCESS**

- Winning variant (strict-equivalence eligible): **`graph_xla_savedmodel`**
- Quantitative gain vs baseline:
  - Mean latency: `0.637590 ms` → `0.331959 ms`
  - Absolute reduction: `0.305631 ms`
  - Relative improvement: **`47.935%`**
- Additional robustness signal:
  - p95 improved from `0.773755 ms` to `0.338665 ms`
  - CV improved from `12.512%` to `1.342%`
