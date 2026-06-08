---
name: lassi-synthesize-verification-report
description: Aggregate the JSON outputs of one or more verification tools (build, assertions, equivalence, fuzz) into a single JSON + markdown report. Use as the final step of a verification run.
allowed-tools:
  - Bash(python cli/lassi-synthesize-verification-report.py*)
  - Bash(python3 cli/lassi-synthesize-verification-report.py*)
  - Read
---

Takes a list (or single dict) of tool-result JSONs and writes a stable `report.json` + `report.md` under `output_dir`, collapsing the per-tool verdicts into an overall verdict.

## Invocation

```
python cli/lassi-synthesize-verification-report.py \
    [--task-id ID] \
    [--task-type C_TO_C_OPTIMIZATION|C_TO_TORCH_TRANSLATION] \
    --tool-results '[{...},{...}]'  |  --tool-results-file results.json \
    [--output-dir .verify/reports]
```

## Example

```
python cli/lassi-synthesize-verification-report.py \
    --task-id foo-2026-06-08 \
    --tool-results-file .verify/foo/tool_results.json \
    --output-dir .verify/reports/foo
```

## Underlying impl

`lassi.verification.verification_tools.synthesize_verification_report_impl`
