# Recovery Changes — Phase 4 Re-implementation (Quantization Recovery)

## Scope Executed

Implemented replanned quantization recovery in [`optimize_variants.py`](soda-benchmarks/models/tensorflow/EELS/optimize_variants.py), kept existing passing variants intact, regenerated manifest/variants, and ran containerized sanity checks only (no final verifier classification run in this phase).

## Quantization Recovery Implementation

### 1) Added float16 TFLite quantization candidate

- Added `float16` quantized export in [`export_tflite_quant_variants()`](soda-benchmarks/models/tensorflow/EELS/optimize_variants.py:179) using `TFLiteConverter` + `supported_types=[tf.float16]`.
- Added new variant ID `ptq_float16_tflite` to manifest output emitted by [`main()`](soda-benchmarks/models/tensorflow/EELS/optimize_variants.py:266).

### 2) Revised int8 calibration coverage (lower-error-risk)

- Replaced simplistic Gaussian-only calibration with a broader representative set in [`_representative_dataset()`](soda-benchmarks/models/tensorflow/EELS/optimize_variants.py:149):
  - multiple Gaussian scales,
  - shifted distributions,
  - structured temporal patterns (ramps/sines/spikes).
- Kept conversion baseline-origin via concrete signature (`from_concrete_functions([infer])`) for dynamic/full int8 in [`export_tflite_quant_variants()`](soda-benchmarks/models/tensorflow/EELS/optimize_variants.py:188).
- Configured revised full-int8 path to allow float I/O with int8 kernel quantization where legal, reducing interface distortion risk.

### 3) Variant flow/manifest plumbing updates

- Variant generation now emits these quantized IDs:
  - `ptq_float16_tflite`
  - `ptq_dynamic_int8`
  - `ptq_full_int8`
- Regenerated [`variant_manifest.json`](soda-benchmarks/models/tensorflow/EELS/LASSI/variant_manifest.json) includes all existing passing SavedModel variants plus revised quantization entries.

### 4) Sanity runner generalized for revised/added quant variants

- Updated [`sanity_check_variants.py`](soda-benchmarks/models/tensorflow/EELS/sanity_check_variants.py:64) to iterate manifest-driven variant sets instead of hard-coded quant IDs.
- This ensures future quantization variants are automatically sanity-checked for runnable status, output contract, and input sensitivity.

### 5) Verifier compatibility prep for new quant variant ID

- Added `ptq_float16_tflite` tolerance class and TFLite handling branch in [`phase5_verify.py`](soda-benchmarks/models/tensorflow/EELS/LASSI/phase5_verify.py:228) and [`phase5_verify.py`](soda-benchmarks/models/tensorflow/EELS/LASSI/phase5_verify.py:310) so Phase 5 can evaluate the new candidate without additional code churn.

## Files Modified

- [`optimize_variants.py`](soda-benchmarks/models/tensorflow/EELS/optimize_variants.py)
- [`sanity_check_variants.py`](soda-benchmarks/models/tensorflow/EELS/sanity_check_variants.py)
- [`LASSI/phase5_verify.py`](soda-benchmarks/models/tensorflow/EELS/LASSI/phase5_verify.py)
- [`LASSI/variant_manifest.json`](soda-benchmarks/models/tensorflow/EELS/LASSI/variant_manifest.json) (regenerated)
- [`LASSI/variant_sanity.json`](soda-benchmarks/models/tensorflow/EELS/LASSI/variant_sanity.json) (regenerated)
- [`LASSI/changes.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/changes.md)

## Containerized Commands Executed

- `docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "python optimize_variants.py"`
- `docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "python sanity_check_variants.py"`

## Sanity Outcomes (Phase-4 only)

- Variant generation command completed successfully and printed manifest including `ptq_float16_tflite`.
- Sanity command completed successfully and produced [`variant_sanity.json`](soda-benchmarks/models/tensorflow/EELS/LASSI/variant_sanity.json).
- All variants report runnable status with expected output contract:
  - input `[1, 240, 1]` `float32`
  - outputs `[1, 16]` (both heads)
- Input sensitivity remained `true` for both outputs across SavedModel and TFLite variants.

## Residual Risks for Phase 5 Verification Retry

1. Quantization drift may still exceed strict per-head tolerances for `z_log_var` on int8 variants despite improved representative coverage.
2. Converter warnings remain present (`from_concrete_functions` deprecation warning and quantized input stats warning) and should be triaged in verifier report.
3. Full-int8 path is still highest-risk; if equivalence fails again, fallback to `ptq_float16_tflite` or non-quantized winner policy from [`refactor-plan.md`](soda-benchmarks/models/tensorflow/EELS/LASSI/refactor-plan.md:365).
