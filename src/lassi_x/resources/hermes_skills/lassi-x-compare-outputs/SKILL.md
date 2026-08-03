---
name: lassi-x-compare-outputs
description: Compare numeric outputs with bounded mismatch diagnostics and mixed absolute/relative tolerances.
version: 1.0.0
author: LASSI-X
license: MIT
platforms: [linux]
requires_toolsets: [terminal]
metadata:
  hermes:
    tags: [LASSI-X, Verification, Numeric]
---
# Compare Numeric Outputs

Run:
`lassi-x output compare --reference REF --candidate CAND --rtol R --atol A --json`

Interpret shape and finite-value failures before numeric errors. Maximum relative error
near zero must be read alongside maximum absolute error and relative L2. Use the bounded
mismatch list to locate indexing, boundary, and update-order mistakes.
