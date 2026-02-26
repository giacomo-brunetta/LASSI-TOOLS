# Phase 7 Final Summary — LASSI Optimization Workflow (EELS)

## Source Artifacts Synthesized

- [`LASSI/phase1_analysis.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/phase1_analysis.md)
- [`LASSI/phase2_baseline.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/phase2_baseline.md)
- [`LASSI/refactor-plan.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/refactor-plan.md)
- [`LASSI/changes.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/changes.md)
- [`LASSI/verification_report.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/verification_report.md)
- [`LASSI/comparison.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/comparison.md)

## Optimization Techniques Attempted and Verification Status

| Technique / Variant | Verification Status | Notes |
|---|---|---|
| FP32 baseline SavedModel (`fp32_baseline_savedmodel`) | `IDENTICAL` | Exact match to golden outputs. |
| Graph/XLA optimized SavedModel (`graph_xla_savedmodel`) | `IDENTICAL` | Exact match; strict-equivalence eligible and performance winner. |
| Mixed precision FP16 SavedModel (`mixed_fp16_savedmodel`) | `ACCEPTABLE_NUMERIC_DRIFT` | Within mixed-precision tolerance; not strict-equivalence winner eligible. |
| Mixed precision BF16 SavedModel (`mixed_bf16_savedmodel`) | `ACCEPTABLE_NUMERIC_DRIFT` | Within mixed-precision tolerance; not strict-equivalence winner eligible. |
| PTQ float16 TFLite (`ptq_float16_tflite`) | `ACCEPTABLE_NUMERIC_DRIFT` | Passed drift policy but excluded from strict-equivalence winner pool. |
| PTQ dynamic int8 (`ptq_dynamic_int8`) | `DIFF_EXISTS` | Failed tolerance for both `z_mean` and `z_log_var`. |
| PTQ full int8 (`ptq_full_int8`) | `DIFF_EXISTS` | Failed tolerance with larger per-head absolute errors. |

## Strict Equivalence Status

- **Workflow strict-equivalence gate (all attempted variants): `FAIL`** due to `DIFF_EXISTS` results in int8 PTQ variants.
- **Final promoted winner strict-equivalence status: `IDENTICAL`** (`graph_xla_savedmodel`).

## Final Performance Winner and Quantitative Gain

From [`LASSI/comparison.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/comparison.md):

- Winner: `graph_xla_savedmodel` (strict-equivalence eligible)
- Baseline mean latency: `0.637590 ms`
- Winner mean latency: `0.331959 ms`
- Absolute gain: `0.305631 ms` reduction
- Relative gain: **`47.935%` improvement**
- Supporting robustness:
  - p95: `0.773755 ms` -> `0.338665 ms`
  - CV: `12.512%` -> `1.342%`

## Rejected Techniques and Reasons

- `ptq_dynamic_int8` rejected: verification `DIFF_EXISTS`; first mismatches and max-abs-error exceeded planned tolerance (`atol=2e-3`) on both heads.
- `ptq_full_int8` rejected: verification `DIFF_EXISTS`; max-abs-error exceeded planned tolerance (`atol=5e-3`) on both heads.
- Drift-only pass variants (`mixed_fp16_savedmodel`, `mixed_bf16_savedmodel`, `ptq_float16_tflite`) were not selected for final winner because strict final selection was constrained to `IDENTICAL` candidates.

## Reproducibility Commands Used (Containerized)

Canonical command template used across phases:

```bash
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "<COMMAND>"
```

Key workflow commands captured in phase artifacts:

```bash
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "python optimize_variants.py"
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "python sanity_check_variants.py"
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "python LASSI/phase5_verify.py 2>&1 | tee LASSI/verification_execution.log"
```

## Cleanup Status

- **Artifacts preserved. No cleanup performed.**
