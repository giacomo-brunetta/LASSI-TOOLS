---
name: lassi-diff-csv-outputs
description: Element-wise mismatch report between two CSVs, optionally written to disk. Use when a comparison failed and you need to know which rows/cols disagree.
allowed-tools:
  - Bash(python cli/lassi-diff-csv-outputs.py*)
  - Bash(python3 cli/lassi-diff-csv-outputs.py*)
  - Read
---

Walks both CSVs element-by-element, returns the first N mismatches with coordinates and values, and can persist the full mismatch list to a JSON file.

## Invocation

```
python cli/lassi-diff-csv-outputs.py --golden-csv PATH --candidate-csv PATH \
    [--output-path mismatches.json] [--max-rows 20]
```

## Example

```
python cli/lassi-diff-csv-outputs.py --golden-csv golden.csv --candidate-csv out.csv --max-rows 50 \
    --output-path .verify/reports/mismatch.json
```

## Underlying impl

`lassi.verification.csv_tools.diff_csv_outputs_impl`
