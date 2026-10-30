# Experiment result status

The [combined accelerator results](accelerator-combined-results-20261028/README.md)
merge the retained previous and additional candidates after ignoring duplicates:
62 starting sources, 82 numerical passes in 186 evaluations, with available timings, source provenance and
measurement gaps. The narrower 32 immediate FP16 plus 13 FP16 repair cohort has
45 entries and 68 numerical passes in 135 accelerator evaluations; the combined
report separates it from BF16 repairs and other historical sources. Duplicates
are excluded from all main totals.

**Start with the [current results handoff](RESULTS-HANDOFF.md)** for retention,
exclusion, corrected-source decisions and the current model scope. It supersedes
older status prose below where they conflict. The Luna/Terra/SOL C-to-Torch
corrections are complete; GPU/numerical continuations remain separate. OSS is
restarted for seven C-to-Torch CPU corrections and 27 pending eligible accuracy
continuations, preserving existing valid results and shared-baseline holds.
The handoff links a source-hashed CPU decision ledger and the
live GPU validity overlays; older frozen snapshots need subsequent holds applied.

The replacement campaigns use the [numerical accuracy policy](numerical-accuracy-policy.md) for
error bands, catastrophic exclusion, repair eligibility, and error/latency frontiers.

## Current clean results

The [conservative LARGE paper subset](paper-usable-snapshot-20261021T181420Z/README.md)
freezes usable baseline and repair observations, separates integer algorithms and
partial improvements, and excludes known semantic counterexamples. Its counts
supersede unfiltered continuation totals for paper use. In particular, Lorenz c1
and its inherited repairs fail a same-size alternate-input C test because their
time step is derived from supplied data; see the frozen counterexample evidence.

The [October 20 retrospective validity audit](result-validity-audit-20261020/README.md)
provides per-candidate retention and exclusion lists for the main CPU campaign,
current LARGE precision baselines and repairs, and the earlier MINI FP16 inventory.
It distinguishes valid target measurements from results that also pass the new
input checks on recorded FP64/FP32 controls. Historical gate acceptance must not
be read as acceptance under the extended checks.

The [corrected-input LARGE continuation](input-corrected-large-20261020/README.md)
revalidates saved implementations with C-derived input fixtures and no model calls.
It reports pending work, newly measured results, and conditional agent retries
separately. Originals and their traces and costs remain preserved; the continuation
does not reconstruct the original agents' counterfactual retry trajectories.

The [October 21 agent repair continuation](input-corrected-agent-repairs-20261021/README.md)
runs verified retry targets with the extended checks, preserving original trials
and recording new model usage separately. The original GPT-OSS repair campaign
has now completed all 59 targets (236/236 trials across its four model arms).

All historical numerical-repair results have been
[retired to legacy](numerical-repairs-retired-20261017.md), including all 52 main
LARGE repair variants. No historical repair subset remains valid. CPU translation
results and current strict GPU porting/validation are separate and remain preserved.

The [frozen CPU results](cpu-results-frozen-20261016.md) report the original
33-kernel Luna, Terra, and GPT-OSS campaigns, with a hashed evidence index.
The later five-kernel policy refresh is frozen separately, not pooled into the
original full-suite success rates. These are CPU FP64 translation outcomes only.

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
