# Legacy experiment results

All experiment artifacts that were already present anywhere under this `runs/`
directory at `2026-09-29T19:12:44Z` are legacy results.

They were produced before the bounded tool-output policy
`bounded-tool-output-v1` was introduced. Unbounded command output could consume
excessive model context during agentic repair, so these results must not be mixed
with, compared directly against, or presented as results from the revised
protocol. This applies to successful, partial, failed, retried, and resumed runs,
including their CPU baselines and all three experimental phases:

1. C to Torch generation and semantic repair.
2. Torch to accelerator/GPU compatibility and measurement.
3. GPU numerical-error diagnosis and compensation.

The artifacts are retained only for provenance and forensic analysis. Re-run the
entire campaign from phase 1 for publishable results; do not resume a legacy run
or seed a new phase from a legacy CPU/Torch baseline.

New runs created after the timestamp above are not automatically legacy. They
must record the revised code revision and policy version so that their provenance
is distinguishable from this corpus.
