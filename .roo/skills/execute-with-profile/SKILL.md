---
name: execute-with-profile
description: Runs an executable and returns both the output and a detailed energy/power profiling report
---

# Execute with Profile Instructions

Use this skill to measure both execution time and energy/power consumption of a binary.

1.  Identify the executable binary.
2.  Provide any necessary command-line arguments.
3.  Ensure the environment supports power measurement (e.g., ARM Power Probe for CPU, NVIDIA Power Probe for GPU).
4.  Optionally provide a path to dump the output or expected output for validation.

## Code Template

```bash
python3 LASSI-TOOLS/skills/execute-with-profile/execute_with_profile.py \
    --path ./my_app \
    --args "--iterations 1000"
```

## Common Issues

- **Hardware/Driver Support**: Power measurement requires specific hardware and drivers (like `nvidia-smi` or ARM-specific probes). If these are missing, the profiler may report zero or error out.
- **Permissions**: Some power measurement tools require elevated permissions.
@
