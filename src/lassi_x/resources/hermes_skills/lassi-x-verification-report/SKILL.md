---
name: lassi-x-verification-report
description: Aggregate arena, correction, compensation, and measurement results into an auditable report.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Reporting, Verification]
---
# Verification Report

Run `lassi-x report verification --run RUN_DIR --json`.
The report must identify the C/C++ FP64 oracle, every candidate and correction attempt,
compensation gates, failed backends, precision roles, stochastic samples, and frontier
membership. Missing evidence is reported as missing, never converted into a pass.
