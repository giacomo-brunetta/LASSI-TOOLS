# Phase 1 Analysis — EELS TensorFlow Model

## Scope and Constraints Observed

- Phase objective: analysis only (no implementation, no benchmarking, no behavior changes).
- Runtime consistency requirement for later phases: execute validation/benchmarking in Docker using:

```bash
docker run -it -v /home/gbrun:/home/gbrun agostini01/soda:latest /bin/bash
```

- Primary runtime entrypoint identified: `python forward_test.py` from the EELS directory.

## 1) Functional Purpose and Current Architecture

The project implements an **EELS encoder** autoencoder branch in TensorFlow/Keras and exports it through an MLIR/HLS flow.

### Model topology (inference-relevant)

From `tfscript.py`:

- Input: `tensor<1x240x1xf32>` (runtime test uses batch 1).
- Encoder stack:
  1. Conv1D(16 filters, kernel 7, stride 2, same)
  2. LeakyReLU(alpha=0.3)
  3. Dropout(0.2)
  4. Conv1D(32 filters, kernel 7, stride 2, same)
  5. LeakyReLU(alpha=0.3)
  6. Dropout(0.2)
  7. Conv1D(32 filters, kernel 3, stride 2, same)
  8. LeakyReLU(alpha=0.3)
  9. Dropout(0.2)
  10. Conv1D(64 filters, kernel 3, stride 2, same)
  11. LeakyReLU(alpha=0.3)
  12. Flatten
  13. Dense(16) => `z_mean`
  14. Dense(16) => `z_log_var`

Current compile path effectively consumes one output (`Identity`) in downstream conversion flow.

### Export/build pipeline

From `Makefile` and generated artifacts:

1. Build/save model and freeze graph (`tfscript.py`).
2. GraphDef -> TF MLIR (`tf-mlir-translate`).
3. TF MLIR -> TOSA (`tf-opt --tf-to-tosa-pipeline`).
4. TOSA -> lower-level IR/LLVM/HLS (included `.mk` scripts).
5. Hardware flow and simulation output under `output/bambu/baseline`.

## 2) Runtime Interface and Measurable Entry Points

### Python/runtime inference interface

- `forward_test.py` loads `output/model/eels_encoder`, resolves `serving_default` signature, generates random input shape `[1, 240, 1]`, runs one forward pass, and prints output tensor metadata and sample values.
- This is the clearest baseline functional invocation for equivalence tests in later phases.

### Build/configuration interfaces

- Model hyperparameters are hardcoded in `tfscript.py` (`INPUT_SHAPE`, `LATENT_SIZE`, filter/kernel sizes, alpha, dropout).
- Make variables define pipeline behavior (`BAMBU_DEVICE`, `BAMBU_MEMPOLICY`, `BAMBU_CLOCK_PERIOD`, target artifacts).

### Measurable artifacts already present

- `output/tf.mlir`
- `output/01_tosa.mlir`
- `output/02_linalg*.mlir`
- `output/05_llvm_baseline.ll`
- `output/forward_kernel_testbench.c`
- Bambu output tree under `output/bambu/baseline`

These provide static analysis anchors for hotspot/cost hypotheses even before live profiling.

## 3) Key Compute Paths and Likely Hotspots

Inspection of generated TOSA and TF MLIR indicates major compute concentration in:

1. **Four strided convolutions** (dominant MAC count):
   - Conv stages progressively transform `240x1 -> 120x16 -> 60x32 -> 30x32 -> 15x64`.
2. **Activation path**:
   - LeakyReLU lowered as compare/select + scaled multiply (`alpha=0.3`), introducing extra elementwise ops and branches.
3. **Final projection**:
   - Flatten + matmul (`960 x 16`) for latent projection output.
4. **Layout/shape ops**:
   - Frequent reshape/transpose around convolution lowering; these can impact memory traffic and scheduling.

Most expensive operations for latency/energy are expected to be Conv2D-lowered kernels and the final matmul.

## 4) Optimization Candidates (for Later Phases)

No optimization is applied in this phase. Candidates below are proposal-only.

### A. Graph-level and compile-level optimization candidates

1. **Inference graph freezing/canonicalization checks**
   - Ensure dropout is fully inactive in serving path and removed from runtime graph.
   - Verify no unnecessary Identity/ExpandDims/Squeeze chains remain after canonicalization.

2. **Operator fusion opportunities**
   - Conv + BiasAdd + LeakyReLU fusion (framework or backend dependent).
   - Reduce extra movement ops (reshape/transpose) when legal.

3. **Scheduling improvements in transform pipeline**
   - Existing `transform.mlir` targets `linalg.batch_matmul` tiling; tune tiling/unroll factors based on measured cache/memory behavior.
   - Consider additional transform patterns for conv-like workloads if supported by downstream pipeline.

### B. Precision and quantization candidates (with examples)

1. **Post-Training Dynamic Range Quantization (TFLite int8)**
   - Lowest integration friction for first experiment.
   - Example direction:
     - Convert SavedModel to TFLite with representative dataset for calibration.
     - Compare int8/dequantized outputs to FP32 baseline under tolerance.

2. **Full Integer Quantization (weights + activations int8)**
   - Better potential energy/latency gains; higher equivalence risk.
   - Needs representative calibration data matching EELS signal distribution.

3. **Quantization-Aware Training (QAT) fallback path**
   - If PTQ quality loss is too high, use QAT to preserve latent encoding fidelity.
   - Requires access to training workflow/data and is likely higher effort.

4. **Mixed precision (FP16/bfloat16)**
   - Candidate where hardware/backend supports efficient FP16/bf16.
   - Must verify numerics in latent space outputs (`z_mean`/downstream-selected output).

### C. Structural/model-level candidates

1. **Pruning/sparsity for Conv/Dense weights**
   - Unstructured pruning can reduce effective compute only if backend exploits sparsity.
   - Structured pruning (channel/filter) is more deployment-friendly but can alter accuracy significantly.

2. **Kernel/channel rebalancing**
   - Reduce channels in earlier/later conv blocks with equivalence/accuracy guardrails.
   - Should be considered only if strict equivalence is relaxed or retraining is allowed.

### D. Hardware-flow-specific candidates

1. **Bambu memory policy/device/clock tuning**
   - Explore `BAMBU_MEMPOLICY` and clock period impact on area/performance/energy tradeoff.
2. **Loop transform refinement**
   - Current transform unroll factors are effectively no-op (`factor=1`); later profiling can justify meaningful unrolling/tiling changes.

## 5) Functional Equivalence Validation Constraints and Risks

### Core equivalence constraints for later phases

1. **Containerized reproducibility**
   - All validation/benchmark execution must run inside the mandated Docker image/mount setup.

2. **Determinism requirements**
   - `forward_test.py` currently uses random input without an explicit seed.
   - Later phases should set deterministic seeds and reuse fixed test vectors to avoid false mismatches.

3. **I/O contract lock**
   - Input shape/dtype: `[1, 240, 1]`, `float32`.
   - Output selection must stay consistent with current exported serving signature and MLIR pipeline output (`Identity`/forward output).

4. **Tolerance policy**
   - FP32 vs FP32 transformed paths can target near-exact match.
   - Mixed precision/quantized paths require documented `(rtol, atol)` and per-output distribution checks.

### Primary risks

1. **Output ambiguity risk**
   - Keras encoder defines two outputs (`z_mean`, `z_log_var`), but build/MLIR flow uses one target output (`Identity`).
   - Later validation must explicitly pin which output is authoritative for equivalence.

2. **Numeric drift risk (quantization/mixed precision)**
   - Latent-space outputs can be sensitive to quantization scale selection and activation clipping.

3. **Graph-lowering semantic drift**
   - Rewrites around transpose/reshape/activation lowering may preserve semantics but alter floating-point accumulation order.

4. **Backend-dependent sparsity gains risk**
   - Pruning may not produce speed/energy benefits if sparse kernels are not exploited by the target flow.

5. **Dropout/training-mode leakage risk**
   - Ensure inference mode behavior is fixed during export and all comparisons.

## 6) Suggested Measurement/Validation Plan Inputs for Next Phases

For profiling/verification phases (not executed here):

- Fixed deterministic test set (multiple representative EELS-like inputs, not random-only).
- Golden baseline run from current implementation in Docker.
- Candidate run under identical Docker invocation, same input tensors, same output extraction.
- Compare exact outputs for FP32-preserving changes; tolerance-based checks for mixed precision/quantized variants.

## 7) Key Assumptions and Unknowns

- Assumption: current intended runtime path is encoder forward inference only.
- Unknown: exact downstream consumer expectations for choosing `z_mean` vs `z_log_var` in this benchmark context.
- Unknown: target hardware execution environment for runtime inference (CPU/GPU/NPU) vs HLS-generated accelerator comparison criteria.
- Unknown: availability/representativeness of calibration dataset for robust PTQ.

---

This Phase 1 artifact is limited to repository-state analysis and optimization/equivalence planning inputs.
