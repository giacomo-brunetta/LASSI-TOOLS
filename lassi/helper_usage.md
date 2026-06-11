# LASSI Helper Usage

## Purpose
Use the helper modules under `lassi/` to avoid rewriting common translation,
verification, artifact-checking, and reporting logic. The `cli/lassi-*`
scripts (driven by the Claude Code skills) and the Pydantic-graph flow in
`graph/graph_flow.py` are the authoritative runtime surface; the modules
below are for in-repo Python scripts (especially generated harnesses).

## Modules

### `lassi.verification.checks`
Use for:
- file existence and non-empty checks
- `.pt` and `.mlir` artifact checks
- MLIR structural checks
- numeric comparison helpers
- input sensitivity checks
- text-output parsing
- normalized diff preparation
- warning scanning

Common functions:
- `assert_file_exists`
- `assert_nonempty_file`
- `check_pt_artifact`
- `check_mlir_contains_func`
- `check_mlir_contains_runtime_args`
- `check_mlir_not_constantized`
- `check_mlir_contains_dialect`
- `compare_arrays_close`
- `summarize_numeric_diff`
- `write_normalized_array`
- `run_text_diff`
- `scan_warning_lines`

### `lassi.analysis.translation_utils`
Use for:
- deterministic seed setup
- tensor/input construction from simple specs
- loading translation modules and variant registries
- selecting/building variants
- toolchain summary formatting
- verification summary assembly
- artifact path naming
- compact MLIR check summaries

Common functions:
- `set_deterministic_seeds`
- `build_tensor_from_spec`
- `build_inputs_from_specs`
- `clone_with_perturbation`
- `load_python_module_from_path`
- `load_variants_registry`
- `build_variant_by_name`
- `assert_selected_variant_present`
- `summarize_toolchain_info`
- `build_variant_result`
- `build_verification_summary`
- `write_json_report`
- `default_pt_output_path`
- `default_mlir_output_path`
- `artifact_paths_for_variant`
- `summarize_mlir_checks`

### `lassi.verification.csv_tools`
Numeric CSV summarization, exact/tolerant comparison, and element-wise
mismatch reporting. Backs the `lassi-summarize-csv` and
`lassi-compare-csv-outputs` CLIs (the latter exposes both summary and
elementwise modes via `--mode`).

### `lassi.integrations.torch_utils`
Shared PyTorch helpers for model export, torch-mlir lowering, and
translation scripts.

Common functions:
- `build_tensor_from_spec`
- `build_inputs_from_specs`
- `build_trace_input`
- `load_module_from_file`

## Required Reuse Policy
- Before writing translation/export/verification boilerplate, inspect these
  helper modules.
- Do not reimplement helper functionality inline when an existing helper
  already covers the need.
- If functionality is missing and is likely to be reused, add a new helper
  in the appropriate `lassi/<subpackage>/` module instead of embedding
  one-off logic in generated scripts.

## CLIs vs Helpers
- Use the `cli/lassi-*` scripts (via the matching skills) for authoritative
  runtime actions and toolchain access:
  - `lassi-get-toolchain-info` (direct CLI — runs `python -c` + `clang --version` style probes)
  - `lassi-export-model-to-pt`
  - `lassi-compile-torch-to-mlir`
- Use Python helpers for reusable in-repo script logic:
  - verification checks
  - parsing
  - report assembly
  - artifact naming
