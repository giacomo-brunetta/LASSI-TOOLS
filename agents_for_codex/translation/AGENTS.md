# LASSI Translation Agent Flow

## Role
You are the single agent for the LASSI C/C++ kernel to PyTorch/TOSA translation workflow.

This flow replaces the prior multi-agent orchestration with one agent. Do not create subtasks, persona handoffs, or extra report chains beyond the artifacts listed here.

## Required User Inputs
- Project directory
- Target kernel
- Optimization target: performance only, or performance plus energy
- Equivalence requirement: binary equivalence, or correctness within tolerance
- Whether quantization is allowed
- Whether multi-threading is allowed
- Whether vectorization is allowed

If any input is missing, ask for it before proceeding.

## Workflow
1. Workspace setup
   - Confirm the project directory.
   - Create `$PROJECT_DIR/LASSI/`.
2. Analysis
   - Inspect the repository, target kernel entrypoint, build path, run path, I/O contract, dtypes, shapes, tolerances, and translation risks.
   - Write:
     - `LASSI/analysis.md`
     - `LASSI/how-to-run.md`
     - `LASSI/refactoring-targets.md`
3. Translation implementation
   - Implement all materially distinct PyTorch candidates that appear semantically equivalent.
   - Before finalizing each candidate, enumerate every material function/op in its execution path and check compatibility wiki support for those ops.
   - Treat unsupported, missing, or ambiguous compatibility results as blockers for that variant until resolved or explicitly accepted by the user.
   - Do not generate `.pt` or `.mlir` artifacts in this step.
   - Write:
     - `LASSI/translation_notes.md`
     - `LASSI/translation_variants.json`
4. Verification
   - Verify every translation candidate directly against the original C/C++ implementation as the oracle whenever available.
   - Use identical inputs and deterministic settings.
   - Prefer CSV-based numeric artifacts and CSV comparison tools when feasible.
   - Classify results as exactly one of:
     - `IDENTICAL`
     - `ACCEPTABLE_NUMERIC_DRIFT`
     - `DIFF_EXISTS`
     - `VERIFY_BLOCKED`
   - Write:
     - `LASSI/verification_report.md`
   - Update `LASSI/failure_log.md` on failure or blockage.
5. Variant selection
   - If more than one candidate passes verification, profile only the passing variants with one identical methodology and select the best variant.
   - If exactly one candidate passes, select it explicitly and continue.
   - Do not proceed to model generation until one verified variant is selected.
   - Write `LASSI/variant_selection.md` when multiple verified variants are compared.
6. Model generation
   - For each verified variant still in scope, generate `.pt` and TOSA `.mlir` artifacts.
   - Call `get_toolchain_info` first when available and record Python, torch, torch-mlir, and LLVM versions.
   - Use LASSI MCP artifact-generation tools when available; use shell or Docker only after concrete MCP failure evidence.
   - Validate artifact existence, non-emptiness, basic MLIR structure, and input dependence.
   - Treat unsupported ops, illegal ops, tracing freezes, constantized MLIR, and similar warnings as blockers until triaged.
   - Write:
     - `LASSI/model_generation.md`
     - variant `.pt` files
     - variant TOSA `.mlir` files
7. Finalization
   - Produce `LASSI/translation_final_summary.md` with:
     - equivalence status
     - variant inventory
     - selected variant
     - profiler comparison summary when multiple variants were evaluated
     - artifact list
     - fallback summary
     - high-risk-op mitigations
     - unresolved risks
   - Ask the user whether to keep or remove temporary artifacts.

## Operating Rules
- Preserve phase order. Do not skip forward.
- The original C/C++ implementation is the correctness oracle when available.
- Preserve all materially distinct viable variants until verification and profiling choose a winner.
- Prefer compact tables, bullets, and JSON over narrative prose.
- Use prior `LASSI/` artifacts as the source of truth; do not restate them unnecessarily.
- Keep reports concise and machine-usable.
- `.pt` and `.mlir` generation belongs to model generation, not translation implementation.
- Keep example inputs static-shape unless dynamic behavior is explicitly required upstream.
- Use explicit dtypes for example inputs.

## Recovery Rules
- Do not run open-ended automatic retry loops.
- Allow one targeted retry inside the current phase only after recording the first concrete error.
- If translation verification fails, repair only the specific failed variants, then re-run downstream phases as needed.
- If profiling cannot select a winner, resolve the evidence gap before moving forward.
- If all verified variants fail export or lowering, route the issue to the earliest owning phase supported by the evidence:
  - translation or operator choice issue: fix translation
  - verification or input-contract issue: fix verification setup
  - local export or lowering issue: retry once in model generation
- Do not treat the workflow as complete until at least one verified variant produces both `.pt` and `.mlir`, unless a hard external blocker is documented.
- If at least one verified variant succeeds and at least one fails in model generation, stop and ask the user whether to keep only the successful variants or start a repair pass for failed ones.
- Use debugger-style investigation only as a last resort, and only when compatibility evidence says the relevant ops should work but the flow still fails.

## Artifact Requirements
- `LASSI/analysis.md`, `LASSI/how-to-run.md`, `LASSI/refactoring-targets.md`
- `LASSI/translation_notes.md`, `LASSI/translation_variants.json`
- `LASSI/verification_report.md`
- `LASSI/variant_selection.md` when multiple verified variants are compared
- `LASSI/model_generation.md`
- `LASSI/translation_final_summary.md`
- `LASSI/failure_log.md` whenever a phase fails or blocks

## Report Constraints
- `translation_notes.md` should stay concise, include toolchain summary, compatibility URIs consulted, per-variant op inventory, smoke checks, and unresolved risks.
- `translation_variants.json` should stay minimal and machine-readable.
- `verification_report.md` should include commands, artifact paths, tolerance, verdict table, warning summary, final classification, and next owner.
- `variant_selection.md` should include compared variants, metrics, selected variant, and rationale.
- `model_generation.md` should include attempted variants, validation result, toolchain summary, tool calls, artifact paths, warning summary, successful variants, failed variants, and whether user direction is needed.

