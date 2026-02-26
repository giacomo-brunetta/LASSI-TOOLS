# Phase 5 Verification Report — EELS Variants

## Scope

- Phase 5 only: functional equivalence verification against baseline SavedModel at `output/model/eels_encoder`.
- Validation executed in container using required canonical launcher.
- Inputs and seeds were fixed and reused for baseline and all candidates.

## Commands Used

Canonical template:

```bash
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "<COMMAND>"
```

Verification execution:

```bash
docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "python LASSI/phase5_verify.py 2>&1 | tee LASSI/verification_execution.log"
```

## Deterministic Settings

- `PYTHONHASHSEED=1234`
- Python `random.seed(1234)`
- NumPy seed `1234`
- TensorFlow seed `1234`
- Persisted inputs: `LASSI/verification_inputs.npz`
  - `x_primary`: shape `(1, 240, 1)`, dtype `float32`
  - `x_secondary`: shape `(1, 240, 1)`, dtype `float32`

## Output Pinning / Contract

- Pinned output order for all comparisons: `z_mean`, then `z_log_var`.
- Baseline SavedModel source output keys were normalized from `['output_1', 'output_0']` to pinned order.
- TFLite outputs were index-mapped to pinned order via minimal mean-absolute-error matching and recorded in artifacts.

## Comparison Policy Applied

- Strict-first rule implemented:
  - integer-only pair comparisons use exact equality only.
  - floating-point comparisons use variant tolerance policy from plan.
- Tolerance classes used:
  - FP32 variants: `rtol=1e-6`, `atol=1e-6`
  - Mixed FP16/BF16 variants: `rtol=5e-3`, `atol=5e-4`
  - PTQ dynamic int8: `rtol=1e-2`, `atol=2e-3`
  - PTQ full int8: `rtol=2e-2`, `atol=5e-3`

Note: baseline-vs-candidate authoritative comparisons were float outputs; no baseline-vs-candidate integer-only pair existed.

## Input-Sensitivity Evidence

All variants showed non-zero output change between `x_primary` and `x_secondary` for both pinned outputs (`candidate_sensitive=true`), so no constantization symptom was observed in this check.

## Warning Triage (from execution logs)

Source: `LASSI/verification_execution.log`

1. `oneDNN custom operations are on ... slightly different numerical results ...`
   - Classification: **benign-but-relevant**
   - Rationale: expected TensorFlow runtime notice; can affect bit-level reproducibility but does not invalidate run.
2. `WARNING: All log messages before absl::InitializeLog() ...`
   - Classification: **benign**
3. XLA service/device initialization + compile info
   - Classification: **informational**
4. `Created TensorFlow Lite XNNPACK delegate for CPU`
   - Classification: **informational**

No blocking runtime exceptions occurred in final verification run.

## Variant Classification and First Concrete Mismatch Evidence

Overall gate: **FAIL**

1. `fp32_baseline_savedmodel` → `IDENTICAL`
   - `z_mean`: exact equal, max abs error `0.0`
   - `z_log_var`: exact equal, max abs error `0.0`

2. `graph_xla_savedmodel` → `IDENTICAL`
   - `z_mean`: exact equal, max abs error `0.0`
   - `z_log_var`: exact equal, max abs error `0.0`

3. `mixed_bf16_savedmodel` → `ACCEPTABLE_NUMERIC_DRIFT`
   - `z_mean`: within tolerance (`rtol=5e-3`, `atol=5e-4`), max abs error `0.0004424154758453369`
   - `z_log_var`: within tolerance (`rtol=5e-3`, `atol=5e-4`), max abs error `0.00027342350222170353`

4. `mixed_fp16_savedmodel` → `ACCEPTABLE_NUMERIC_DRIFT`
   - `z_mean`: within tolerance (`rtol=5e-3`, `atol=5e-4`), max abs error `4.374980926513672e-05`
   - `z_log_var`: within tolerance (`rtol=5e-3`, `atol=5e-4`), max abs error `6.419233977794647e-05`

5. `ptq_float16_tflite` → `ACCEPTABLE_NUMERIC_DRIFT`
   - `z_mean`: within tolerance (`rtol=5e-3`, `atol=5e-4`), max abs error `9.780377149581909e-05`
   - `z_log_var`: within tolerance (`rtol=5e-3`, `atol=5e-4`), max abs error `0.00014030933380126953`

6. `ptq_dynamic_int8` → `DIFF_EXISTS`
   - First mismatch `z_mean`: index `[0,13]`, golden `-0.21395565569400787`, candidate `-0.21110716462135315`
   - First mismatch `z_log_var`: index `[0,14]`, golden `-0.0871882438659668`, candidate `-0.08411537110805511`
   - Tolerance failures:
     - `z_mean` max abs error `0.002848491072654724` (`rtol=1e-2`, `atol=2e-3`) → not within tolerance
     - `z_log_var` max abs error `0.003072872757911682` (`rtol=1e-2`, `atol=2e-3`) → not within tolerance

7. `ptq_full_int8` → `DIFF_EXISTS`
   - First mismatch `z_mean`: index `[0,10]`, golden `-0.09252965450286865`, candidate `-0.10732241719961166`
   - First mismatch `z_log_var`: index `[0,3]`, golden `-0.08727728575468063`, candidate `-0.07892212271690369`
   - Tolerance failures:
     - `z_mean` max abs error `0.014792762696743011` (`rtol=2e-2`, `atol=5e-3`) → not within tolerance
     - `z_log_var` max abs error `0.008355163037776947` (`rtol=2e-2`, `atol=5e-3`) → not within tolerance

## Reproducibility Artifacts

- `LASSI/verification_results.json`
- `LASSI/verification_execution.log`
- `LASSI/verification_inputs.npz`
- `LASSI/verification_artifacts/baseline_golden_primary.json`
- `LASSI/verification_artifacts/baseline_golden_secondary.json`
- `LASSI/verification_artifacts/<variant>/candidate_primary.json`
- `LASSI/verification_artifacts/<variant>/candidate_secondary.json`
- `LASSI/verification_artifacts/<variant>/comparison_primary.json`

## Final Gate Decision

- Per-variant classifications:
  - `fp32_baseline_savedmodel`: `IDENTICAL`
  - `graph_xla_savedmodel`: `IDENTICAL`
  - `mixed_bf16_savedmodel`: `ACCEPTABLE_NUMERIC_DRIFT`
  - `mixed_fp16_savedmodel`: `ACCEPTABLE_NUMERIC_DRIFT`
  - `ptq_float16_tflite`: `ACCEPTABLE_NUMERIC_DRIFT`
  - `ptq_dynamic_int8`: `DIFF_EXISTS`
  - `ptq_full_int8`: `DIFF_EXISTS`
- Overall verification gate status: **FAIL**.
