# Benchmarks

This directory holds benchmark examples, inputs, and reference implementations. Campaign
scripts and model/backend configurations live in [experiments](../experiments/README.md).
Generated results belong in the configured output directory, outside these sources.

| Directory | Contents |
| --- | --- |
| `polybench/` | [PolyBench/C 4.2.1](https://github.com/MatthiasJReisinger/PolyBenchC-4.2.1): 30 kernels and shared utilities (Git submodule) |
| `rodinia/` | [Rodinia 3.1](https://github.com/yuhc/gpu-rodinia): CUDA, OpenCL, and OpenMP benchmarks (Git submodule) |
| `npb/` | [NAS Parallel Benchmarks 3.0](https://github.com/benchmark-subsetting/NPB3.0-omp-C): OpenMP C implementation (Git submodule) |
| `scientific/` | Eight deterministic scientific C fixtures plus mutual information |

The external suites are pinned Git submodules, declared in [`.gitmodules`](../.gitmodules),
with commit IDs recorded in this repository's Git tree. Initialize them with:

```sh
git submodule update --init --recursive
git submodule status
```

GitHub displays each dependency as a link to its pinned repository commit. GitHub
Actions initializes the submodules before running quality checks. Each suite retains
its own upstream license and build instructions. Rodinia's large input datasets
require a separate download described in its upstream README.

The CPU suite selects 24 PolyBench kernels and nine scientific kernels by default
(33 total); `--full-polybench` includes all 39. See the
[suite instructions](../experiments/cpu-generation/README.md). Rodinia and NPB are
reference examples, outside this integrated suite.

The PolyBench submodule replaces the formerly copied source tree at the same base
revision, `3e872547cef7e5c9909422ef1e6af03cf4e56072`. It uses upstream `3mm.c`.
The former tree's [source manifest](provenance/polybench-vendored-source-manifest.json)
and [local 3mm optimization patch](provenance/polybench-3mm-local.patch) are preserved
for historical reproducibility. To reconstruct that modified source explicitly:

```sh
git -C benchmarks/polybench apply --unidiff-zero ../provenance/polybench-3mm-local.patch
```

Run this command from the repository root. Applying the patch makes the submodule
dirty; new experiments must record the actual source hashes and validate their
inputs independently of historical results.
