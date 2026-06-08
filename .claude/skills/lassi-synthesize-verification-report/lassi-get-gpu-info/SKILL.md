---
name: lassi-get-gpu-info
description: Retrieve GPU information using whichever vendor tool is available — nvidia-smi, rocm-smi, xpu-smi, or `system_profiler SPDisplaysDataType` on macOS / Apple Silicon (reports chip name, vendor, core count, Metal family, attached displays). Use when the user asks what GPU is in the machine, its memory, or driver version.
allowed-tools:
  - Bash(python cli/lassi-get-gpu-info.py*)
  - Bash(python3 cli/lassi-get-gpu-info.py*)
---

Probes whatever SMI tool is available on the host and returns the parsed GPU description. Returns plain text — typically including device name, memory, and driver version.

## Invocation

```
python cli/lassi-get-gpu-info.py
```

No arguments.

## Underlying impl

`lassi.integrations.hardware_info.get_gpu_info_impl`
