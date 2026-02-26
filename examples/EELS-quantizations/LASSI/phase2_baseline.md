# Phase 2 Baseline Profiling — EELS TensorFlow (Original Implementation)

## Scope

- Baseline only (no optimization, no model-logic changes).
- Containerized execution only, using the required canonical pattern.
- Runtime path profiled: forward pass through SavedModel signature from the existing EELS implementation.

## Container Methodology (Reproducible)

Working directory inside container:

- /home/gbrun/soda-benchmarks/models/tensorflow/EELS

Canonical launcher used:

- docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc "<COMMAND>"

Benchmark protocol:

- Determinism controls: numpy seed = 1234, TensorFlow seed = 1234.
- Input tensor fixed across iterations: shape (1, 240, 1), dtype float32.
- Warmup: 10 iterations.
- Measured iterations per repeat: 50.
- Repeats per run: 7.
- Two full runs were captured because run-to-run noise exceeded low-variance expectation.

## Exact Commands Executed

### 1) Baseline latency run #1 + TensorFlow profile capture

- docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc 'python - <<"PY" ... writes LASSI/baseline_latency_run1.json and LASSI/tf_profile_run1 ... PY'

### 2) Energy interface probe + Python call-level profile

- docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc '... writes LASSI/energy_probe.txt and LASSI/baseline_cprofile_run1.txt ...'

### 3) Baseline latency run #2 (retry for variance reporting)

- docker run --rm -v /home/gbrun:/home/gbrun -w /home/gbrun/soda-benchmarks/models/tensorflow/EELS agostini01/soda:latest /bin/bash -lc 'python - <<"PY" ... writes LASSI/baseline_latency_run2.json ... PY'

## Results

### Latency (per-inference milliseconds)

Run 1 (LASSI/baseline_latency_run1.json):

- mean: 0.73898 ms
- median: 0.74300 ms
- min/max: 0.67543 / 0.78909 ms
- stdev: 0.03615 ms
- CV: 4.89%

Run 2 (LASSI/baseline_latency_run2.json):

- mean: 0.62210 ms
- median: 0.58300 ms
- min/max: 0.54216 / 0.85136 ms
- stdev: 0.09684 ms
- CV: 15.57%

Run-to-run variance summary:

- Mean delta (run2 vs run1): -0.11688 ms (about -15.82%).
- Interpretation: measurable noise/outlier sensitivity present; run 2 includes a large first-repeat outlier.
- Planning baseline reference (single-point): report both run means and use their midpoint as a neutral comparison anchor = 0.68054 ms/inference.

### Energy metrics

- No usable RAPL energy counter files were visible from the benchmark container context during this phase.
- Probe found powercap directories but no readable energy_uj endpoints in the scanned locations.
- Therefore, direct energy baseline is marked unavailable for this run configuration.

## Profiling / Callgraph Context

### GPROF applicability

- Standard gprof/callgraph is not directly applicable to this Python + TensorFlow eager/saved-model execution path (no native C/C++ binary compiled with -pg in this phase).

### Alternative hotspot evidence collected

1) Python call-level profile (200 forward invocations):

- Dominant cumulative region is TensorFlow eager execute bridge, with most time under tensorflow.python._pywrap_tfe.TFE_Py_Execute.
- Evidence file: LASSI/baseline_cprofile_run1.txt.

2) TensorFlow profiler trace captured:

- Trace repository emitted at LASSI/tf_profile_run1/plugins/profile/<timestamp>/...xplane.pb.

### Hotspot summary for planning handoff

- Runtime is execution-kernel dominated (TensorFlow backend execution path), not Python loop dominated.
- Based on phase-1 graph analysis and this phase runtime evidence, expected compute-heavy regions remain:
  - Conv stack (four strided Conv1D layers).
  - Final dense projection (matmul-heavy latent heads).
  - Supporting elementwise activation/memory-movement operations.

## Artifacts Produced

- LASSI/baseline_latency_run1.json
- LASSI/baseline_latency_run2.json
- LASSI/baseline_cprofile_run1.txt
- LASSI/energy_probe.txt
- LASSI/tf_profile_run1/plugins/profile/...
- LASSI/phase2_baseline.md

## Baseline Status

- Baseline captured for original implementation under required containerized methodology.
- Latency baseline available with retry/variance evidence.
- Energy baseline unavailable in this container context due to missing readable counters.
