---
name: lassi-x-machine-info
description: Inspect CPU, memory, operating system, architecture, and available execution tools.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Hardware]
---
# Machine Information

Run `lassi-x inspect machine --json` before selecting hardware-sensitive strategies.
Use the reported architecture, core count, memory, and executable availability; never
assume x86, CUDA, or a particular compiler.
