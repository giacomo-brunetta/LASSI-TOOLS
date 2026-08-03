---
name: lassi-x-summarize-output
description: Summarize a numeric CSV or NPY artifact by shape, element count, finite values, range, distribution, and norm. Use for initial output triage, detecting malformed or unstable results, and deciding which detailed comparison to run next.
license: MIT
metadata:
  hermes:
    tags: [Numeric, Diagnostics, Data-Quality]
    requires_toolsets: [terminal]
---
# Summarize Numeric Output

## Role

Act as a numerical data triage analyst. Establish whether an output is structurally plausible and
finite, then use summary statistics to guide diagnosis without mistaking them for equivalence.

## Workflow

1. Run `lassi-x output summarize --path OUTPUT --json`.
2. Check load success, shape, element count, NaN count, and Inf count first.
3. For finite data, inspect minimum, maximum, mean, standard deviation, and L2 norm.
4. Compare the observed scale and shape with the kernel's expected live outputs.
5. If validation is required, follow with an elementwise comparison against the authoritative
   reference output.

## Evidence standard

Report the source path, shape, count, finite-value status, range, distribution statistics, and any
reason the artifact is unsuitable for further comparison.

## Guardrails

- Never treat matching summaries as elementwise or semantic equivalence.
- Never ignore NaN or Inf because other statistics look plausible.
- Never reshape, truncate, or sanitize the artifact during diagnosis.
