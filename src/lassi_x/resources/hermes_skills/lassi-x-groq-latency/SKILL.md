---
name: lassi-x-groq-latency
description: Submit and interpret Groq queue measurements with explicit precision capabilities and failure states.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Groq, Accelerator, Benchmarking]
---
# Groq Measurement

Use `lassi-x groq submit` and `lassi-x groq status`, or run the configured unified flow.
On the connected host run `lassi-x groq worker`. Distinguish measured latency, compiler
estimate, unsupported operations, no-fit, timeout, and crash. Never infer explicit FP32
tensor support merely from a wider matrix accumulator.
