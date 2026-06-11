---
name: lassi-compare-csv-outputs
description: Compare a candidate CSV against a golden CSV. Default mode returns a tolerant pass/fail verdict (max abs/rel error, classification). `--mode elementwise` returns a per-cell mismatch list. Use when verifying that a translation/optimization preserves numeric output.
allowed-tools:
  - Bash(python cli/lassi-compare-csv-outputs.py*)
  - Bash(python3 cli/lassi-compare-csv-outputs.py*)
  - Read
---

Single CLI with two output modes:

- **`--mode summary`** (default) — emits shape match, exact_match, allclose, max_abs_error, max_rel_error, the worst-element coordinates, and a classification (`IDENTICAL` / `ACCEPTABLE_NUMERIC_DRIFT` / `DIFF_EXISTS`). Use this as the pass/fail gate.
- **`--mode elementwise`** — emits a JSON list of per-cell mismatches (up to `--max-rows`, default 20) with row/col + golden vs candidate values + abs diff. Optionally persisted via `--output-path`. Use this when the summary verdict failed and you need to know *which* cells diverged.

## Invocation

```
python cli/lassi-compare-csv-outputs.py \
    --golden-csv PATH --candidate-csv PATH \
    [--mode summary|elementwise] \
    [--rtol 1e-6] [--atol 1e-6] \
    [--expected-shape '[3,4]' | --expected-shape-file shape.json] \
    [--output-path mismatches.json] [--max-rows 20]
```

## Examples

Pass/fail gate:

```
python cli/lassi-compare-csv-outputs.py --golden-csv golden.csv --candidate-csv out.csv --rtol 1e-5
```

Investigate a failure:

```
python cli/lassi-compare-csv-outputs.py --golden-csv golden.csv --candidate-csv out.csv \
    --mode elementwise --max-rows 50 --output-path .verify/reports/mismatch.json
```

## Underlying impl

`lassi.verification.csv_tools.compare_csv_outputs_impl` (summary) and
`lassi.verification.csv_tools.diff_csv_outputs_impl` (elementwise).
