---
name: lassi-x-summarize-output
description: Summarize a numeric CSV or NPY output for shape, range, distribution, NaN, and Inf.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Numeric, Diagnostics]
---
# Summarize Numeric Output

Run `lassi-x output summarize --path OUTPUT --json`.
Check shape and finite values first, then min/max, mean, standard deviation, and norm.
This is diagnostic only; it does not replace comparison with the C/C++ oracle.
