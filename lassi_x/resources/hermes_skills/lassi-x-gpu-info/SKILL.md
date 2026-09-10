---
name: lassi-x-gpu-info
description: Inspect available NVIDIA, AMD, Intel, or Apple accelerators and runtime support. Use before selecting a GPU backend, precision strategy, compensation method, or interpreting an unsupported hardware measurement.
license: MIT
metadata:
  hermes:
    tags: [GPU, Hardware, Capability-Audit]
    requires_toolsets: [terminal]
---
# Inspect GPU Capabilities

## Role

Act as an accelerator capability auditor. Establish what hardware and vendor runtime are
actually visible to this process; do not substitute assumptions based on the host name or model
configuration.

## Workflow

1. Run `lassi-x inspect gpu --json`.
2. Record each vendor probe, detected device, memory, driver, and utility availability.
3. Distinguish “no accelerator,” “vendor utility unavailable,” and “runtime cannot use device.”
4. Use explicit backend capability declarations and measured dtype behavior when selecting
   FP16/BF16 strategies.

## Evidence standard

Report the command result and the exact capability relevant to the decision. Treat unavailable
vendor tooling as an unsupported backend, not as a failure of unrelated pipeline stages.

## Guardrails

- Do not assume CUDA, a specific GPU generation, or native BF16 support.
- Do not infer operator or accumulator precision from storage dtype alone.
- Do not fabricate capability details when a probe is unavailable.
