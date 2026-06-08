---
name: lassi-run-roofline-analysis
description: Combine benchmark timing + workload model + hardware model into a roofline analysis (single or differential). Use after lassi-run-benchmark and lassi-estimate-workload-model to see where each kernel sits relative to compute/memory ceilings. The hardware model JSON is generated internally by the roofline impl when needed; you don't run a separate skill for it.
allowed-tools:
  - Bash(python cli/lassi-run-roofline-analysis.py*)
  - Bash(python3 cli/lassi-run-roofline-analysis.py*)
  - Read
---

Reads the three artifact JSONs and emits a roofline report: achieved GFLOP/s, achieved bandwidth, and percent-of-peak at the chosen precision/memory level.

> **Important:** the internal hardware-model probe returns 0 peak FLOPs / 0 peak bandwidth on hardware it can't introspect (most macOS hosts, many ARM SoCs, sandboxed environments). When peaks are 0 the roofline math collapses and the verdict comes back **UNSURE**. To work around it, pass `manual_overrides` so the impl has real peaks to compare against:
>
> ```bash
> # When invoking lassi-collect-hardware-model is unavailable as a skill,
> # construct the hardware model JSON yourself:
> cat > hw.json <<EOF
> {"peak_flops": {"fp32": 1.2e13}, "peak_bandwidth_Bps": {"dram": 4.0e11}}
> EOF
> python cli/lassi-run-roofline-analysis.py --hardware-model-path hw.json ...
> ```
>
> Peak numbers come from the vendor (e.g. Apple M-series Geekbench results, NVIDIA whitepaper TFLOPS, DRAM bandwidth from `dmidecode` × channels). Better an approximate manual peak than 0.

## Invocation

```
python cli/lassi-run-roofline-analysis.py \
    --benchmark-result-path bench.json \
    --workload-model-path workload.json \
    --hardware-model-path hw.json \
    [--precision fp32] [--memory-level dram] [--mode single|differential] \
    [--artifact-dir DIR] [--policy '{...}']
```

## Example

```
python cli/lassi-run-roofline-analysis.py \
    --benchmark-result-path .perf/bench.json \
    --workload-model-path .perf/workload.json \
    --hardware-model-path .perf/hw.json \
    --precision fp32 --memory-level dram --mode differential
```

## Underlying impl

`lassi.profiling.performance_tools.run_roofline_analysis_impl`
