---
name: lassi-estimate-workload-model
description: Estimate FLOPs, bytes moved, and arithmetic intensity per benchmark case (formula / manual / static-analysis / agent-assisted). Use before roofline analysis to characterize what each kernel actually does.
allowed-tools:
  - Bash(python cli/lassi-estimate-workload-model.py*)
  - Bash(python3 cli/lassi-estimate-workload-model.py*)
  - Read
---

For each case (matching the run_benchmark case_id), computes the FLOPs and bytes the kernel performs and the resulting arithmetic intensity. `formula` mode is implemented for common kernels (gemm, conv, etc.); `manual` uses per-case `manual_flops`/`manual_bytes` from the case metadata.

## Invocation

```
python cli/lassi-estimate-workload-model.py \
    --benchmark-cases '[...]'  |  --benchmark-cases-file cases.json \
    [--source-a PATH] [--source-b PATH] \
    [--estimation-mode formula|manual|static_analysis|agent_assisted] \
    [--artifact-dir DIR]
```

## Example

```
python cli/lassi-estimate-workload-model.py --benchmark-cases-file .perf/cases.json \
    --estimation-mode formula
```

## Underlying impl

`lassi.profiling.performance_tools.estimate_workload_model_impl`
