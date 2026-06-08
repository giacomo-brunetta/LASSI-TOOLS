---
name: lassi-compare-csv-outputs
description: Compare a candidate CSV against a golden CSV with rtol/atol tolerances and report match status plus error metrics. Use when verifying that a translation/optimization preserves numeric output.
allowed-tools:
  - Bash(python cli/lassi-compare-csv-outputs.py*)
  - Bash(python3 cli/lassi-compare-csv-outputs.py*)
  - Read
---

Loads both CSVs, compares them exactly and with tolerances, and emits a JSON verdict including max abs/rel error and the location of the worst element.

## Invocation

```
python cli/lassi-compare-csv-outputs.py --golden-csv PATH --candidate-csv PATH [--rtol 1e-6] [--atol 1e-6] \
    [--expected-shape '[3,4]' | --expected-shape-file shape.json]
```

## Example

```
python cli/lassi-compare-csv-outputs.py --golden-csv golden.csv --candidate-csv out.csv --rtol 1e-5
```

## Underlying impl

`lassi.verification.csv_tools.compare_csv_outputs_impl`
