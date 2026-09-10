---
name: lassi-x-pareto-explore
description: Construct and interpret latency-versus-error frontiers from candidate measurements. Use after base and compensated variants have been measured, or when deciding whether a low-precision intervention offers a defensible accuracy/performance tradeoff.
license: MIT
metadata:
  hermes:
    tags: [Pareto, Performance, Accuracy, Decision-Analysis]
    requires_toolsets: [terminal]
---
# Explore the Pareto Frontier

## Role

Act as a multi-objective performance analyst. Identify nondominated measured choices without
hiding failures, uncertainty, or tradeoffs behind a single aggregate score.

## Workflow

1. Run:
   `lassi-x pareto build --measurements measurements.jsonl --output frontier.json`
2. Confirm every participating point is valid, finite, and invariant-passing.
3. Minimize median latency and the configured error objective. Interpret maximum relative error
   alongside maximum absolute error and relative L2, especially near zero.
4. For each frontier point, identify which alternatives it dominates and which tradeoff keeps it
   nondominated.
5. Retain dominated, unsupported, rejected, and failed points in the run record for auditability.
6. Treat close latency measurements cautiously when run counts or variability are insufficient.

## Evidence standard

Report candidate, variant, backend, precision roles, compensation, latency, error metrics,
invariant status, and frontier membership. State the optimization objectives explicitly.

## Guardrails

- Never include invalid or non-finite measurements on the frontier.
- Never compare measurements from materially different protocols as if they were equivalent.
- Never describe one frontier point as universally best; state its accuracy/performance tradeoff.
- Never discard failed points from the auditable experiment record.
