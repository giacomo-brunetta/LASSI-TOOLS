---
name: lassi-x-groq-latency
description: Submit, execute, and interpret Groq queue measurements with explicit precision capabilities and failure states. Use when a candidate must be measured on a Groq-connected host or when distinguishing measured latency from compiler estimates, unsupported operations, no-fit, timeout, and crash results.
license: MIT
metadata:
  hermes:
    tags: [Groq, Accelerator, Benchmarking, Remote-Queue]
    requires_toolsets: [skills]
---
# Measure on Groq

## Role

Act as a remote accelerator benchmark operator. Preserve request identity and backend evidence
across disconnected submitter and worker hosts, and classify every terminal state honestly.

## Workflow

1. Before submission, run `lassi-x-compat-wiki targets` and select the exact
   Groq/compiler snapshot matching the requested stack; never silently substitute A100 or Torch-MLIR/TOSA results. Inventory the
   candidate's expected `aten.*` operators. Query uncertain or nontrivial operators with
   `lassi-x-compat-wiki op OPERATOR --target TARGET --precision fp16` and search alternatives with
   `lassi-x-compat-wiki search PATTERN --target TARGET --precision fp16 --supported`.
2. Treat `compile_rejected` as evidence to investigate and repair the implicated formulation.
   Missing snapshots, `needs_fixture`, `not_applicable`, and unknown operators leave support
   unverified; they do not establish a candidate defect. Record the gap once. If the assigned
   tools and experiment budget permit, resolve it with an exact-target compiler probe; otherwise
   report the limitation and stop submission. Treat a compiled canonical case only as
   operator-level evidence, not proof that the complete model will compile, place, or execute.
3. Submit the fully specified request with `lassi-x groq submit` or use the configured pipeline.
4. Record the request ID, module hash, queried operators, compatibility results, precision roles,
   backend name, and submission time.
5. On the connected host, run the configured `lassi-x groq worker` with the intended executor.
6. Poll with `lassi-x groq status`; do not submit duplicates merely because execution is slow.
7. Require each measured latency to carry finite accuracy computed from LPU output for the same
   compiled model, static inputs, dataset, and oracle. Reject latency-only completion records.
8. Classify the result as measured, compiler estimate, unsupported, no-fit, timeout, or crash.
9. Include only valid paired device latency/error points in performance comparisons unless
   estimates are clearly labeled and analyzed separately.

## Diagnostics

Follow the [diagnostic output policy](../references/diagnostics.md).
Report request state, the root compiler/runtime diagnostic, and its implicated operator or phase.

## Evidence standard

Report request ID, source identity, queried operators and wiki results, precision capabilities,
evaluation dataset and oracle, device-output accuracy, latency provenance, execution state, and
compiler/runtime diagnostics. Keep failed requests in the experiment record.

## Guardrails

- Never present a compiler estimate as measured hardware latency.
- Never accept latency without a finite oracle comparison from the paired LPU evaluation.
- Never infer explicit FP32 tensor support from a wider matrix accumulator.
- Never silently retry with a different graph, precision, or compiler configuration.
- Never collapse unsupported, no-fit, timeout, and crash into one generic failure.
- Never present compatibility-wiki support as measured Groq compatibility.
