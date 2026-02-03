---
name: get-machine-info
description: Retrieves CPU and RAM information for the current machine
---

# Get Machine Info Instructions

Use this skill to understand the hardware capabilities of the system you are working on.

1.  Run the script to get a JSON report of CPU (counts, frequency, usage) and RAM (total, available, used).

## Code Template

```bash
python3 ~/LASSI-TOOLS/.roo/skills/get-machine-info/get_machine_info.py
```

## Common Issues

- **psutil Missing**: Ensure the `psutil` library is installed.
