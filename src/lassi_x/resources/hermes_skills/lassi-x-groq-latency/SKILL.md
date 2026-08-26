---
name: lassi-x-groq-latency
description: Submit, execute, and interpret Groq queue measurements with explicit precision capabilities and failure states. Use when a candidate must be measured on a Groq-connected host or when distinguishing measured latency from compiler estimates, unsupported operations, no-fit, timeout, and crash results.
license: MIT
metadata:
  hermes:
    tags: [Groq, Accelerator, Benchmarking, Remote-Queue]
    requires_toolsets: [terminal]
---
# Measure on Groq

## Role

Act as a remote accelerator benchmark operator. Preserve request identity and backend evidence
across disconnected submitter and worker hosts, and classify every terminal state honestly.

## Workflow

1. Before submission, run `lassi-x-compat-wiki targets` and select the closest exact
   Groq/compiler snapshot; never silently substitute A100 or legacy results. Inventory the
   candidate's expected `aten.*` operators. Query uncertain or nontrivial operators with
   `lassi-x-compat-wiki op OPERATOR --target TARGET --precision fp16` and search alternatives with
   `lassi-x-compat-wiki search PATTERN --target TARGET --precision fp16 --supported`. If a
   TorchScript artifact is available, run `lassi-x-compat validate MODEL_PATH` to check its
   discovered operator set.
2. Treat a rejected or unknown exact-target result as a preflight failure requiring candidate
   repair. Treat a compiled canonical case only as operator-level evidence, not proof that the
   complete model will compile, place, or execute.
3. Submit the fully specified request with `lassi-x groq submit` or use the configured pipeline.
4. Record the request ID, module hash, queried operators, compatibility results, precision roles,
   backend name, and submission time.
5. On the connected host, run the configured `lassi-x groq worker` with the intended executor.
6. Poll with `lassi-x groq status`; do not submit duplicates merely because execution is slow.
7. Classify the result as measured, compiler estimate, unsupported, no-fit, timeout, or crash.
8. Include only valid measured latency in performance comparisons unless estimates are clearly
   labeled and analyzed separately.

## Evidence standard

Report request ID, source identity, queried operators and wiki results, precision capabilities,
execution state, latency provenance, and compiler/runtime diagnostics. Keep failed requests in the
experiment record.

## Guardrails

- Never present a compiler estimate as measured hardware latency.
- Never infer explicit FP32 tensor support from a wider matrix accumulator.
- Never silently retry with a different graph, precision, or compiler configuration.
- Never collapse unsupported, no-fit, timeout, and crash into one generic failure.
- Never present compatibility-wiki support as measured Groq compatibility.
