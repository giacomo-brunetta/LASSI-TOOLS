# A100 Luna/Terra numerical-compensation campaign

> **LEGACY — rerun required.** This campaign predates bounded tool-output policy
> `bounded-tool-output-v1`. Retain it only for provenance and forensic analysis;
> do not publish its results, resume its runs, reuse its baselines, or combine its
> measurements with the replacement campaign. See [the experiment status
> note](README.md).

Campaign: `a100-terra-cpu-baseline-ablation-20260926-compensation`

Completed on September 27, 2026 after selective retries for provider-limit interruptions. All 58 planned Luna/Terra entries started from checksummed, CPU-verified Torch baselines. The campaign plan SHA-256 is `06b52ca53010293c1363044d6f085aa5a3641893c51696afeb832b09fa205ed3`.

Latest outcome counts:

- 14 `ok`
- 42 `partial`
- 2 `failed`

`partial` is retained as a measured accelerator/numerical outcome, not an infrastructure failure. It can include valid precision measurements, divergence evidence, or incomplete compatibility/compensation repair. The final selective retry reran only Terra `polybench-nussinov`; it finished `ok` with 24 measurements and no usage-limit error.

The per-entry latest outcomes, immutable run-directory references, and measurement counts are recorded in `a100-terra-cpu-baseline-ablation-20260926-compensation.csv`. Raw generated campaign artifacts remain intentionally ignored under `runs/` because they include large, reproducible execution workspaces.
