# Benchmarks

This directory holds benchmark inputs and reference implementations. Campaign
scripts and model/backend configurations live in [experiments](../experiments/README.md).
Generated results belong in the configured output directory, outside these sources.

| Directory | Contents |
| --- | --- |
| `polybench/` | All 30 PolyBench/C 4.2.1 kernels, shared utilities, and upstream license |
| `scientific/` | Eight deterministic scientific C fixtures plus mutual information |
| `polybench-3mm/` | MINI/MEDIUM precision headers and PyTorch regression fixtures |
| `polybench-jacobi-2d/` | Precision header for the Jacobi configuration |

The CPU suite selects 24 PolyBench kernels and nine scientific kernels by default
(33 total); `--full-polybench` includes all 39. See the
[suite instructions](../experiments/cpu-generation/README.md).

The PolyBench files were copied from the existing local checkout, preserving its
tracked source contents, including its modified `3mm.c`. They are not asserted to
be pristine upstream sources. [source-manifest.json](polybench/source-manifest.json)
records the checkout revision and SHA256 of every copied file. Local optimized
variants, executables, and run outputs were excluded. PolyBench retains its
[upstream license](polybench/LICENSE.txt).
