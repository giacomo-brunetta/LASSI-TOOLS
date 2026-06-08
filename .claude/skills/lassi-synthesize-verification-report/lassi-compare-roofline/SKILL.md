---
name: lassi-compare-roofline
description: Compare reference vs candidate roofline positions/utilization from a roofline_report.json. Use to judge whether an optimization moved a kernel closer to its peak (or off the roof entirely).
allowed-tools:
  - Bash(python cli/lassi-compare-roofline.py*)
  - Bash(python3 cli/lassi-compare-roofline.py*)
  - Read
---

Takes a `roofline_report.json` (output of lassi-run-roofline-analysis with `--mode differential`) and applies the comparison policy to render a verdict per case.

## Invocation

```
python cli/lassi-compare-roofline.py \
    --roofline-result-path roofline_report.json \
    [--policy '{...}' | --policy-file policy.json] \
    [--artifact-dir DIR]
```

## Example

```
python cli/lassi-compare-roofline.py --roofline-result-path .perf/roofline_report.json
```

## Underlying impl

`lassi.profiling.performance_tools.compare_roofline_impl`
