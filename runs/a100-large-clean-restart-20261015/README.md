# Clean LARGE restart — prepared, not run

All 33 kernels and their 96 available original Terra CPU seeds are frozen here. IIR filter bank, Durbin and Deriche have two available seeds each; the other kernels have three. No numerical/compatibility repair output has been adopted as a clean baseline. References and sizes come from the stopped LARGE campaign, not the older size sweep.

Historical diagnostics flag 20 kernels / 32 kernel-precision pairs (25 failed, 7 weak at relative L2 > 0.01). These are provisional candidates, not a definitive count at the frozen workload. The old sweep selected one implementation per precision, including repaired MINI sources, at different sizes.

Before repair: independently validate all 96 frozen bases, including high-precision semantic gates, then measure the 192 FP16/BF16 cells and audit actual arithmetic. Separate numerical failures from timeout/OOM/compiler failures. Previously passing full-FP32 implementations are not low-precision successes.

The intended policy is recorded in baseline-inventory.json. Prompts now implement this policy; runtime precision auditing is still pending. No agent campaign has been started.

## Provisional targets from historical LARGE diagnostics

| Kernel | Precisions |
|---|---|
| iir-filter-bank | bf16 |
| low-rank-compression | bf16, fp16 |
| poisson-cg | bf16, fp16 |
| polybench-3mm | fp16 |
| polybench-adi | bf16, fp16 |
| polybench-atax | bf16, fp16 |
| polybench-cholesky | bf16, fp16 |
| polybench-correlation | fp16 |
| polybench-covariance | fp16 |
| polybench-deriche | fp16 |
| polybench-durbin | bf16, fp16 |
| polybench-fdtd-2d | bf16, fp16 |
| polybench-floyd-warshall | bf16, fp16 |
| polybench-gemver | fp16 |
| polybench-gramschmidt | bf16, fp16 |
| polybench-jacobi-2d | bf16, fp16 |
| polybench-lu | fp16 |
| polybench-seidel-2d | bf16, fp16 |
| softened-nbody | bf16 |
| wavelet-compression | bf16, fp16 |
