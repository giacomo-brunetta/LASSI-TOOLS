---
name: lassi-summarize-csv
description: Summarize a numeric CSV file (shape, range, mean/std, NaN/Inf presence). Use when the user wants a quick sanity check on a kernel's CSV output.
allowed-tools:
  - Bash(python cli/lassi-summarize-csv.py*)
  - Bash(python3 cli/lassi-summarize-csv.py*)
  - Read
---

Inspects a numeric CSV and returns its shape, element count, min/max, mean/std, and whether it contains NaN or Inf entries.

## Invocation

```
python cli/lassi-summarize-csv.py --path PATH
```

## Example

```
python cli/lassi-summarize-csv.py --path examples/kernels/foo/output.csv
```

## Underlying impl

`lassi.verification.csv_tools.summarize_csv_impl`
