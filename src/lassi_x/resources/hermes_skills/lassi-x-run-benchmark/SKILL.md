---
name: lassi-x-run-benchmark
description: Measure a validated PyTorch candidate with warmups, repeated trials, synchronized accelerator timing, and oracle-relative error reporting. Use after semantic validation when comparing candidates, precisions, backends, or compensation variants.
license: MIT
metadata:
  hermes:
    tags: [Benchmarking, Performance, Measurement]
    requires_toolsets: [terminal]
---
# Run a Stable Benchmark

## Role

Act as a performance measurement engineer. Produce reproducible latency evidence without changing
the implementation, overlapping device work, or separating speed from numerical validity.

## Workflow

1. Confirm the module has passed the authoritative semantic gate.
2. Run:
   `lassi-x benchmark run --config CONFIG --module MODULE --backend NAME --precision PRECISION`
3. Verify the reported backend, device, storage/operator/accumulator/output precision, source
   identity, warmup count, iteration count, and synchronization behavior.
4. Check validity, finite outputs, oracle-relative errors, and scientific invariant alongside
   timing. A fast invalid point is not a performance result.
5. Compare median latency using equivalent protocols. Use minimum latency as supporting evidence,
   not the primary result.

## Evidence standard

Report module, backend, device, precision roles, warmups, repetitions, median and minimum latency,
error metrics, equivalence, invariant status, and terminal status.

## Guardrails

- Never benchmark before semantic validation.
- Never overlap measurements on the same physical device.
- Never compare unsynchronized accelerator time with synchronized time.
- Never omit precision roles or report invalid output as a speedup.
