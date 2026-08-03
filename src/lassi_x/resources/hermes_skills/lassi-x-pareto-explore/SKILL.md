---
name: lassi-x-pareto-explore
description: Construct and interpret latency-versus-error frontiers from LASSI-X measurements.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Pareto, Performance, Accuracy]
---
# Pareto Exploration

Run `lassi-x pareto build --measurements measurements.jsonl --output frontier.json`.
Only finite, valid, invariant-passing points participate. Minimize median latency and
maximum relative error; interpret the latter with absolute error and relative L2 near zero.
Keep dominated and failed points in the run record for auditability.
