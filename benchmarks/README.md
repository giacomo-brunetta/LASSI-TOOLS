# Benchmarks

This directory holds benchmark examples, inputs, and reference implementations. Campaign
scripts and model/backend configurations live in [experiments](../experiments/README.md).
Generated results belong in the configured output directory, outside these sources.

| Directory | Contents |
| --- | --- |
| `polybench/` | [PolyBench/C 4.2.1](https://github.com/MatthiasJReisinger/PolyBenchC-4.2.1): 30 kernels and shared utilities (Git submodule) |
| `rodinia/` | [Rodinia 3.1](https://github.com/yuhc/gpu-rodinia): CUDA, OpenCL, and OpenMP benchmarks (Git submodule) |
| `npb/` | [NAS Parallel Benchmarks 3.0](https://github.com/benchmark-subsetting/NPB3.0-omp-C): OpenMP C implementation (Git submodule) |
| `npb-3.4.4/` | [Preserved NPB 3.4.4 import](https://github.com/KeyLiaoHPC/TacVar): NASA OpenMP/MPI sources under `suites/NPB3.4.4/` (Git submodule) |
| `itk/` | [Official ITK](https://github.com/InsightSoftwareConsortium/ITK): mutual information example and production metrics (Git submodule) |
| `randlapack/` | [RandLAPACK](https://github.com/BallisticLA/RandLAPACK): randomized SVD and low-rank approximation (Git submodule) |
| `parboil/` | [Preserved Parboil mirror](https://github.com/palmer-dabbelt/parboil): includes MRI-Gridding (Git submodule) |
| `scientific/` | Eight deterministic scientific C fixtures plus mutual information |

The external suites are pinned Git submodules, declared in [`.gitmodules`](../.gitmodules),
with commit IDs recorded in this repository's Git tree. Initialize them with:

```sh
git submodule update --init
git submodule update --init --recursive benchmarks/randlapack third_party/herbie third_party/tenspiler
git submodule status
```

GitHub displays each dependency as a link to its pinned repository commit. GitHub
Actions initializes the submodules before running quality checks. The explicit nested
dependency command avoids an unrelated, malformed `suites/lmbench` Git link in
the preserved NPB import (its upstream `.gitmodules` has no URL). Do not use a
blanket recursive update with that import. Each suite retains
its own upstream license and build instructions. Rodinia's large input datasets
require a separate download described in its upstream README.

The requested 40-workload source cohort is frozen in
[the source manifest](provenance/workloads-40.json): all 30 PolyBench kernels;
NPB CG, MG, and FT; Rodinia LavaMD, Myocyte, DWT2D, and CFD; ITK mutual
information; RandLAPACK randomized SVD; and Parboil MRI-Gridding. The manifest
records suite URLs, full commit IDs, and SHA-256 hashes of representative source
entry points. Entire suites remain available, including shared dependencies and
alternative implementations; the manifest counts each workload once.

NPB 3.4.4 is separate from the historical `npb/` C port. NASA distributes the
[official release as an archive](https://www.nas.nasa.gov/software/npb.html).
The pinned TacVar commit is its original import, before instrumentation changes:
all 378 retained release files match NASA's archive byte for byte; only
`Changes.log` is missing. The manifest records the official archive URL and hash.
The repository also contains unrelated TacVar/lmbench material outside the NPB
source subtree. CG, MG, and FT in this release are Fortran, with OpenMP and MPI
variants.

For the additional single workloads, start at ITK's
`Examples/Statistics/ImageMutualInformation1.cxx`, RandLAPACK's
`RandLAPACK/drivers/rl_rsvd.hh` and `test/drivers/test_rsvd.cc`, and Parboil's
`benchmarks/mri-gridding/src/base/`. Rodinia DWT2D is available under `cuda/dwt2d/`
and `opencl/dwt2d/`; the other selected Rodinia workloads also have OpenMP sources.
RandLAPACK's RandBLAS dependency is a nested pinned submodule.

This inventory acquires sources only. It does not add these workloads to the
integrated CPU suite, build them, run experiments, or establish correctness.
Follow each upstream project's license, dependency, build, and dataset instructions.

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
