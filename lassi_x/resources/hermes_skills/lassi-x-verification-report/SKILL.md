---
name: lassi-x-verification-report
description: Aggregate oracle, arena, correction, compensation, measurement, failure, and Pareto evidence into an auditable verification record. Use after a completed or failed run when summarizing what was attempted, what passed, and what evidence remains missing.
license: MIT
metadata:
  hermes:
    tags: [Reporting, Verification, Audit]
    requires_toolsets: [terminal]
---
# Produce a Verification Report

## Role

Act as an independent verification evidence auditor. Reconstruct the run from artifacts and make
the distinction between pass, fail, unsupported, and missing evidence impossible to overlook.

## Workflow

1. Run `lassi-x report verification --run RUN_DIR --json`.
2. Confirm the report identifies the original C/C++ FP64 oracle, reference path, output artifact,
   and run configuration.
3. Account for every planned candidate, generation status, correction attempt, diagnostic, model,
   provider, and usage record.
4. Account for every compensation variant, selected technique, FP64 gate, FP32-collapse gate,
   target-precision result, and correction attempt.
5. Account for every backend/precision cell, failure state, precision role, stochastic sample,
   invariant result, and Pareto membership.
6. Reconcile totals with the raw run and measurement artifacts. Mark absent or contradictory
   evidence explicitly.

## Evidence standard

Every conclusion must point to a recorded artifact or structured field. Report passed gates,
failed gates, unsupported cells, missing evidence, and unresolved contradictions separately.

## Guardrails

- Never convert missing evidence, an unsupported backend, or a crashed agent into a pass.
- Never omit rejected candidates or dominated variants from the audit trail.
- Never describe FP16/BF16 results without their storage, operator, accumulator, and output roles.
- Never claim end-to-end success when the authoritative oracle or frontier is absent.
