---
name: push-callgraph-to-memory
description: Runs gprof to generate a callgraph and pushes it to the Memory MCP server for long-term storage and analysis
---

# Push Callgraph to Memory Instructions

Use this skill to persist the structural relationship of functions in your code into a knowledge graph.

1.  Identify the source files.
2.  Provide compilation and execution details.
3.  Ensure the Memory MCP server (running in Docker) is accessible.
4.  The skill will compile the code with profiling, execute it, parse the gprof output, and upload it.

## Code Template

```bash
python3 ~/LASSI-TOOLS/.roo/skills/push-callgraph-to-memory/push_callgraph_to_memory.py \
    --path main.cpp \
    --compiler g++ \
    --args "test_input.txt"
```

## Common Issues

- **Docker Not Running**: This skill depends on a Docker-based Memory MCP server. Ensure Docker is installed and running.
- **gprof Missing**: Ensure `gprof` is installed on the system.
