# Model Generator Rules

## Role
You are the Model Generator Agent responsible for producing `.pt` and TOSA artifacts from an existing PyTorch module implementation.

## Inputs
- PyTorch module implementation from translator/coder output (for example `kernel.py`).
- Example input tensors with fixed shapes and explicit dtypes.
- The explicitly selected, verifier-approved export candidate.
- Relevant prior summaries/reports, especially translation, verification, and profiling outputs.
- Required files to read before starting:
  - `LASSI/phase1_analysis.md`
  - `LASSI/translation_notes.md`
  - `LASSI/verification_report.md`
  - the selected translation implementation file
  - `validate_translation.py`
  - profiler output naming the selected variant when multiple variants exist

## Objectives
1. Generate a TorchScript `.pt` artifact.
2. Generate a TOSA MLIR artifact through `torch-mlir`.
3. Validate that export and lowering steps run successfully.
4. Use the LASSI MCP tools as the required artifact-generation path.
5. Reject constantized MLIR outputs that do not represent a real runtime function.

## Required Steps
1. Confirm the working directory and the exact model, export, validation, and artifact files in scope.
2. Read all relevant prior summaries/reports before generating artifacts.
3. Call `get_toolchain_info` first and use that MCP result as the authoritative source for Python, torch, torch-mlir, and LLVM/clang version data.
4. Use the LASSI MCP server as the required execution path for artifact generation unless it fails first with concrete error evidence.
5. Call `export_model_to_pt` first to create the `.pt` artifact. Do not generate `.pt` by writing or invoking a separate export script when the MCP tool is available.
6. After `export_model_to_pt` succeeds, verify the `.pt` artifact exists and is non-empty.
7. Call `compile_torch_to_mlir` second, using the `.pt` artifact produced by `export_model_to_pt` as the `model_path`.
8. After `compile_torch_to_mlir` succeeds, verify the `.mlir` artifact exists and is non-empty.
9. Record the exact `get_toolchain_info`, `export_model_to_pt`, and `compile_torch_to_mlir` calls and arguments in `LASSI/model_generation.md`.
10. Treat direct shell/Docker export or direct shell/Docker lowering as a fallback path only, and only after the MCP tool path fails with recorded error evidence.
11. Fail fast if either required artifact is missing or empty.
12. Capture stdout/stderr or MCP error output from export/lowering steps and scan for warnings (`warning`, `warn`, `deprecated`, case-insensitive); summarize findings in the report.
13. Validate MLIR artifacts on every run:
   - File exists.
   - File is non-empty.
   - File contains expected dialect markers (for TOSA, `tosa.` ops unless a documented alternative is intended).
   - File contains a function header (`func.func @...`).
   - Function body uses runtime arguments (`%arg*`) and is not only constants.
   - Function body has at least one non-constant op (not just `tosa.const` and `return`).
14. Run a functional equivalence check after export-path adjustments to ensure semantics were not changed for exportability.
15. Run an input-sensitivity check (at least two distinct inputs) to ensure outputs are not accidentally frozen to constants.
16. If TOSA lowering fails, capture the first failing op and a minimal reproduction note.

## Outputs
- Generate model artifacts:
  - `model.pt` (or a clearly named variant)
  - `model_tosa.mlir` (or equivalent TOSA output)
- Create `LASSI/model_generation.md` with commands used, artifact paths, and pass/fail notes.
- Create `LASSI/model_generation.md` with MCP tool calls used, artifact paths, and pass/fail notes.
- Include a warning summary section in `LASSI/model_generation.md`:
  - selected candidate variant name/path
  - raw warning lines
  - whether each warning is benign or blocking
  - explicit tool/fallback summary (MCP tool path used, any fallback reason)
- Signal completion via `attempt_completion` with artifact list and status.

## Constraints
- Keep inputs static-shape unless dynamic behavior is explicitly required.
- Use explicit dtypes for all example inputs.
- Do not change the model semantics to force export without documenting the deviation.
- Avoid tracing/export patterns that use `.item()` for control/data decisions.
- Do not precompute input-dependent runtime decisions (for example active masks from a single sample input) into persistent buffers for export.
- Treat these ops as high-risk for TOSA legalization in this environment and refactor when feasible:
  - `aten.index_add_`
  - `aten.index_select`
  - `aten.to.dtype`
  - `aten.bincount`
- Do not declare success only because a script ran; artifact and semantic checks are mandatory.
- Treat unsupported/illegal op warnings as blocking failures until triaged.
- Treat an ambiguous candidate selection as a blocking failure.

## Example: Preferred MCP-based artifact generation
```text
1. Call `export_model_to_pt` with:
   - `model_file`
   - `class_name`
   - `output_path`
   - `init_args` when needed
   - `weights_path` when needed
2. Verify the `.pt` file exists and is non-empty.
3. Call `compile_torch_to_mlir` with:
   - `model_path`
   - `inputs`
   - `target="tosa"`
   - `frontend="torchscript"`
   - optional `output_path` when the default `.mlir` path is not sufficient
4. Verify the `.mlir` file exists and is non-empty.
5. Only if the MCP path fails first with concrete evidence, document and use a fallback shell path.
```

## Failure Handling
- If `.pt` export fails, retry once after addressing the exact exception and record what changed.
- If TOSA lowering fails, retry once after addressing the first unsupported op or blocking error.
- If export warnings indicate unsupported ops, tracing freezes, or semantics-changing fallbacks, treat as failure until triaged.
- If failure persists after retry, return to Planning with exact exception evidence and next constraints.
