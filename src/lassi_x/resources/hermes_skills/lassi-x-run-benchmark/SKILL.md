---
name: lassi-x-run-benchmark
description: Measure a validated PyTorch candidate with warmups, repetitions, and synchronized CUDA timing.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Benchmarking, Performance]
---
# Run a Stable Benchmark

Run `lassi-x benchmark run --config CONFIG --module MODULE --backend NAME --precision fp16`.
Benchmark only after semantic validation. Never overlap measurements on the same physical
device. Report median latency together with minimum, run count, precision roles, and errors.
