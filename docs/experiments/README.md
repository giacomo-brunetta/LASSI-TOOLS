# Experiment result status

The replacement campaigns use the [numerical accuracy policy](numerical-accuracy-policy.md) for
error bands, catastrophic exclusion, repair eligibility, and error/latency frontiers.

## Current clean results

The Luna and Terra MINI C-to-Torch CPU-verification campaigns completed under
`bounded-tool-output-v1`. The results are recorded in
[the medium-effort model comparison](c-to-torch-model-comparison-medium-20261002.md).
This is phase 1 only; accelerator and numerical-correction phases have not been run
for these campaigns. The raw run corpus and hashed manifests remain in ignored
`runs/cpu-luna-medium-20261002-retry2/` and
`runs/cpu-terra-medium-20261002-retry2/` directories in the originating workspace.

> **Legacy-results notice (September 29, 2026):** Every result generated before
> `2026-09-29T19:12:44Z`, and every report or figure in this directory derived
> from those results, is legacy. These artifacts are retained for provenance and
> forensic analysis only; they are not publishable results under the current
> protocol.

The earlier campaigns predate bounded tool-output policy
`bounded-tool-output-v1`. In particular, agent commands could return complete
graphs, tensors, logs, and traces to the model. That behavior could exhaust model
context or provider quota during repair and makes the old and revised protocols
non-equivalent.

The complete experiment campaign must therefore be rerun from phase 1:

1. C to Torch across the model matrix, starting from the original C/Terra inputs.
2. Torch to GPU/accelerator across the model matrix, using only newly generated
   and verified phase-1 outputs.
3. GPU numerical-error correction across the model matrix, using only the new
   phase-2 runs.

Do not resume an old run, reuse an old CPU/Torch baseline, or combine old and new
measurements. New reports must record the code revision and the tool-output policy
version. The ignored raw corpus is marked recursively by `runs/LEGACY.md` and
`runs/LEGACY.json` in the working tree.

## Legacy published artifacts

- `legacy/a100-terra-cpu-baseline-ablation-20260926-compensation.md`
- `legacy/a100-terra-cpu-baseline-ablation-20260926-compensation.csv`
- `legacy/figures/cpu-model-success-rates.json`
- `legacy/figures/cpu-model-success-rates.svg`
- `legacy/figures/precision-error-before-after.png`
- `legacy/figures/precision-error-before-after.prompt.txt`

This list is a status declaration, not a deletion: the historical values remain
available to explain prior decisions and diagnose the quota failure.
