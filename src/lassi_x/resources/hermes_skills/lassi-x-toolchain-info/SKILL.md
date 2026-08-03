---
name: lassi-x-toolchain-info
description: Report Python, PyTorch, compiler, CUDA, Hermes, and LASSI-X versions.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Toolchain, Reproducibility]
---
# Toolchain Information

Run `lassi-x inspect toolchain --json`. Include this record with experimental results.
Version mismatch is diagnostic evidence; do not silently switch interpreters or compilers.
