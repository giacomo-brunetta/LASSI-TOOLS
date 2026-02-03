---
name: get-gpu-info
description: Retrieves information about detected GPUs using SMI tools (NVIDIA, AMD, Intel)
---

# Get GPU Info Instructions

Use this skill to identify available GPU hardware and its current utilization.

1.  Run the script. It will automatically detect if `nvidia-smi`, `rocm-smi`, or `xpu-smi` is available and output the relevant information.

## Code Template

```bash
python3 LASSI-TOOLS/skills/get-gpu-info/get_gpu_info.py
```

## Common Issues

- **No SMI Tool**: If no GPU management tool is installed, the skill will report that no dedicated GPU tools were found. This usually means no supported GPU is present or drivers are missing.
