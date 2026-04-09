# LASSI Helper Usage

## Purpose
Use the helper modules in `lassi/` to avoid rewriting common translation, verification,
artifact-checking, and reporting logic.

## Modules

### `lassi.check_utils`
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

### `lassi.translation_utils`
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

## Required Reuse Policy
- Before writing translation/export/verification boilerplate, inspect these helper modules.
- Do not reimplement helper functionality inline when an existing helper already covers the need.
- If functionality is missing and is likely to be reused, add a new helper in `lassi/` instead of embedding one-off logic in generated scripts.

## MCP Tools vs Helpers
- Use MCP tools for authoritative runtime actions and Docker-backed toolchain access:
  - `get_toolchain_info`
  - `export_model_to_pt`
  - `compile_torch_to_mlir`
- Use Python helpers for reusable in-repo script logic:
  - verification checks
  - parsing
  - report assembly
  - artifact naming

## Future Schema Design
If helper schemas are added later, expose them through a resource template such as:
- `helpers://schema/check_utils/check_mlir_contains_func`
- `helpers://schema/translation_utils/build_verification_summary`

Recommended implementation:
- define per-function metadata and optional Pydantic models
- expose JSON schema and short usage notes through a resource template
- keep this overview file as the first resource agents read
