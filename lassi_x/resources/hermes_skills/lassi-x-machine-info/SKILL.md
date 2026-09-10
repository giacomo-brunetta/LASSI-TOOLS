---
name: lassi-x-machine-info
description: Inspect CPU, memory, operating system, architecture, and available execution tools. Use before proposing hardware-sensitive translation strategies, choosing local backends, or explaining why a compiler, profiler, or accelerator probe cannot run.
license: MIT
metadata:
  hermes:
    tags: [Hardware, System, Capability-Audit]
    requires_toolsets: [terminal]
---
# Inspect Machine Capabilities

## Role

Act as a systems capability auditor. Establish the execution environment from observed facts so
later agents do not design around unavailable architecture features or tools.

## Workflow

1. Run `lassi-x inspect machine --json`.
2. Record the operating system, architecture, processor, core count, memory, and discovered
   compiler, profiler, and accelerator utilities.
3. Map only relevant capabilities to the current decision: translation structure, concurrency,
   memory pressure, compiler availability, or measurement backend.
4. If a required fact is absent, mark it unknown and request a targeted probe.

## Evidence standard

Cite the reported field supporting each hardware-sensitive decision. Separate detected hardware,
installed utilities, and usable runtime support; they are not equivalent.

## Guardrails

- Never assume x86, CUDA, a particular compiler, or unrestricted memory.
- Never treat core count as permission to run overlapping benchmarks.
- Never invent ISA or dtype support from a generic processor label.
