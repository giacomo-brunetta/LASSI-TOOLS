---
name: lassi-run-assertion-suite
description: Execute a generated `assertion_suite.py` against two implementation artifacts and report pass/fail per assertion. Use after lassi-generate-assertion-suite, which writes the suite that this skill runs.
allowed-tools:
  - Bash(python3 *)
  - Read
---

`generate_assertion_suite` writes a self-contained Python file (`assertion_suite.py`) that imports a shared `common_harness.py` and runs assertions through `harness.run_a / harness.run_b`. The suite reads its two artifacts and the harness path from environment variables.

## Required environment

| Variable | Value |
|---|---|
| `LASSI_HARNESS_PATH` | Absolute path to the directory containing `common_harness.py` |
| `IMPLEMENTATION_A_ARTIFACT` | Path to the reference artifact (`.py` module or `.so` shared lib) |
| `IMPLEMENTATION_B_ARTIFACT` | Path to the candidate artifact (same kind as A) |

## Invocation

```bash
LASSI_HARNESS_PATH=/abs/path/.verify/harnesses/<task_id> \
IMPLEMENTATION_A_ARTIFACT=/abs/path/build/foo_baseline.so \
IMPLEMENTATION_B_ARTIFACT=/abs/path/build/foo_v2.so \
    python3 /abs/path/.verify/assertions/<task_id>/assertion_suite.py
```

stdout is a JSON object: `{"assertions_run": N, "failures": [...], "a_failures": N, "b_failures": N}`. Exit code is `0` on no failures, `1` otherwise.

## Notes

- `LASSI_HARNESS_PATH` must be the **directory** that contains `common_harness.py` — the suite does `sys.path.insert(0, parent)` and then `import common_harness`.
- The suite is generated for a specific entrypoint name + signature; if the artifacts don't expose the expected symbol, the suite raises at `harness.configure(...)` before running any assertion.
- For Python module artifacts pass the `.py` file directly; the harness loads it with `importlib`.
