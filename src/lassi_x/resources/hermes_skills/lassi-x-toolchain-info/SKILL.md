---
name: lassi-x-toolchain-info
description: Report Python, package, compiler, and accelerator-toolchain versions and availability. Use when recording a reproducible experiment, diagnosing environment-dependent behavior, or checking whether the configured interpreter and compiler stack can execute the pipeline.
license: MIT
metadata:
  hermes:
    tags: [Toolchain, Reproducibility, Environment]
    requires_toolsets: [terminal]
---
# Inspect the Toolchain

## Role

Act as a reproducibility auditor. Capture the exact software environment that can affect source
generation, compilation, tensor execution, accelerator behavior, and measurements.

## Workflow

1. Run `lassi-x inspect toolchain --json` from the same environment used for the pipeline.
2. Record the Python executable and version; installed package versions for the translation,
   agent, validation, and tensor stack; and compiler or accelerator tools.
3. Distinguish “not installed,” “not on PATH,” and “probe failed.”
4. Attach the record to experimental results and cite relevant differences during diagnosis.

## Evidence standard

Report exact observed versions and command status. If a component is absent, preserve that fact
instead of substituting a version from another environment.

## Guardrails

- Never silently switch interpreters, environments, compilers, or accelerator runtimes.
- Never infer compatibility solely because a package imports.
- Never omit version mismatches that could change numerical or performance results.
