# Local reproduction result

Run date: 2026-07-30

Environment:

- Python 3.12.13
- Hermes Agent 0.19.0
- PyTorch 2.12.0
- GCC 13.3.0
- NVIDIA GB10

The checked-in independent candidate passed the original C FP64 oracle gate.
Its maximum absolute FP64 difference was `2.220446049250313e-16`.

## Full Hermes arena

Run artifact:
`runs/polybench-3mm/20260730T202231.573908Z-polybench-3mm-mini`

The complete run finished successfully in 392.265 seconds:

- planner: Claude Opus 4.8 through Argo;
- candidate 1: GPT-4.1, vectorized initialization and `matmul`;
- candidate 2: Gemini 2.5 Pro, broadcast initialization and `einsum`;
- candidate 3: Claude Sonnet 5, loop-faithful initialization and explicit buffers;
- compensation: Claude Opus 4.7.

All three independently generated candidates passed the original C FP64 gate
on their first external validation attempt. The arena selected eight weak
FP16/BF16 backend cells and produced eight compensation variants; all eight
passed the C FP64 and FP32-collapse gates. The run recorded 88 valid
measurements and two Pareto-frontier points.

Representative candidate-1 baseline measurements:

| Backend | Precision | Median latency | Maximum relative error |
|---|---:|---:|---:|
| CPU | FP64 | 4.54 µs | 3.74e-16 |
| CPU | FP32 | 4.40 µs | 3.02e-7 |
| CPU | FP16 | 626.84 µs | 7.40e-4 |
| CPU | BF16 | 907.05 µs | 6.53e-3 |
| CUDA | FP64 | 38.91 µs | 4.43e-16 |
| CUDA | FP32 | 22.83 µs | 1.42e-7 |
| CUDA | FP16 | 20.52 µs | 7.40e-4 |
| CUDA | BF16 | 20.36 µs | 6.53e-3 |

These MINI timings are dominated by launch and framework overhead and should
not be interpreted as large-kernel throughput results.

The strongest numerical compensation result was candidate 2 on CUDA BF16.
FP32 accumulation reduced maximum relative error from `6.5346e-3` to
`3.1607e-3` (51.6% lower), with median latency increasing from 37.88 µs to
59.90 µs. Other compensated variants illustrate that compensation is not
automatically beneficial: some reduced relative-L2 error while slightly
worsening maximum relative error, and several CUDA variants added latency.

The global MINI frontier contained candidate 1 CPU FP64 and CPU FP32. The
small matrices make CPU FP32 both faster and more accurate than the
low-precision alternatives, so no compensated point reached this particular
frontier.

The Argo credential is obtained at runtime by executing the `apiKeyHelper` in
`~/.claude/settings.json`; the credential is not copied into configuration or
run artifacts.

To reproduce:

```bash
cd /home/gbrun/LASSI-X
lassi-x run examples/polybench-3mm/run.yaml
```
