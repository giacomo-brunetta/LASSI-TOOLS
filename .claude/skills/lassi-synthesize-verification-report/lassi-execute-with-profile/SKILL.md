---
name: lassi-execute-with-profile
description: Run a binary with Timer + CPU/GPU power probes (Arm/Nvidia where available) and report the combined profile. Use when the user wants power/energy data alongside latency.
allowed-tools:
  - Bash(python cli/lassi-execute-with-profile.py*)
  - Bash(python3 cli/lassi-execute-with-profile.py*)
---

Same as lassi-execute-with-latency, but additionally attempts to attach ArmPowerProbe (CPU) and NvidiaPowerProbe (GPU). Unavailable probes are reported in the "Probe Warnings" section rather than aborting the run.

## Invocation

```
python cli/lassi-execute-with-profile.py --path BIN [--args 'a b c'] \
    [--dump-output stdout.txt] [--expected-output PATH_OR_STRING]
```

## Example

```
python cli/lassi-execute-with-profile.py --path ./build/sgemm --args '512 512 512'
```

## Underlying impl

`lassi.core.executer.ExecTool` + `MultiProfiler([Timer, CPUProfiler(ArmPowerProbe), GPUProfiler(NvidiaPowerProbe)])`
