---
name: gprof-profiling
description: Compiles source file(s) with gprof instrumentation and returns the callgraph/flat profile
---

# Gprof Profiling Instructions

Use this skill to identify performance bottlenecks in C/C++/CUDA code by generating a profile report.

1.  Identify the main source file and any additional source files.
2.  Specify the compiler to use.
3.  Add any necessary compiler flags (gprof `-pg` flags are added automatically by the underlying tool).
4.  Provide arguments that should be passed to the program during the profiling run.

## Code Template

```bash
python3 ~/LASSI-TOOLS/.roo/skills/gprof-profiling/gprof_profiling.py \
    --path main.cpp utils.cpp \
    --compiler g++ \
    --args "input_data.txt"
```

## Common Issues

- **Execution Failure**: If the program crashes during execution, gprof will not be able to generate a profile.
- **No gmon.out**: Ensure the program terminates normally; otherwise, the profiling data might not be written.
