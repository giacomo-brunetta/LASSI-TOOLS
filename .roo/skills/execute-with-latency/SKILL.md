---
name: execute-with-latency
description: Runs an executable and returns both the output and the execution time (latency)
---

# Execute with Latency Instructions

Use this skill to measure the execution time of a binary and optionally verify its output.

1.  Identify the executable binary.
2.  Provide any necessary command-line arguments.
3.  Optionally provide a path to dump the output.
4.  Optionally provide expected output for functional validation.

## Code Template

```bash
python3 LASSI-TOOLS/skills/execute-with-latency/execute_with_latency.py \
    --path ./my_app \
    --args "--iterations 1000" \
    --expected_output golden.txt
```

## Common Issues

- **Executable Not Found**: Ensure the path to the binary is correct and it has execution permissions.
- **Validation Failure**: If `expected_output` is provided and the actual output differs, the tool will report a mismatch.
