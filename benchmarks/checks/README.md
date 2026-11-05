# Random-input correctness cases for all 39 workloads

Every workload in `../provenance/workloads-39.json` has an explicit C fixture
entry point and five seeded random cases. Production preparation goes directly
to **LARGE** and keeps its dimensions fixed across seeds 0–4. Each exact input
is imported into the trusted native computation to regenerate expected outputs,
and the same contract goes to the candidate. Every candidate revision must pass
every case. There is no size progression or primary-only acceptance.

## Source files stay unchanged

Original kernel files in the pinned benchmark submodules are read-only. Fixture
instrumentation must never be applied in place. The harness reads the original
and compiles a generated `<run_dir>/oracle/c-fixture/reference.c` containing
input/output hooks around the computation. Run/build artifacts belong outside
source submodules. See the [instrumentation contract](../../docs/c-fixtures.md#original-source-preservation-and-generated-instrumentation).

Versioned fixture entry points, bridges and the PolyBench allocator shim are
separate files under `benchmarks/checks/`. Their
changes require their own validation; they do not replace or overwrite upstream
kernel files. NPB subroutine copies and parameter headers are generated only in
the artifact build directory. Original source hashes and pinned commits remain
the reference identities and must match before preparation/preflight proceeds.

## Prepare dependencies and cases

Initialize submodules using `docs/development.md`. Native prerequisites are a C/C++
compiler, CMake, gfortran and BLAS/LAPACK. On Ubuntu install `cmake gfortran
libopenblas-dev`; on Apple Silicon install `cmake gcc libomp` with Homebrew.
The pinned BLAS++, LAPACK++ and Random123 sources are submodules. Build their
libraries and the minimal ITK module closure in an explicit directory:

```sh
uv run --locked --extra dev --extra globus --extra roofline \
  python tools/prepare_workload_dependencies.py build/workload-native --jobs 4
uv run --locked --extra dev --extra globus --extra roofline \
  python -m lassi_x.workload_checks /absolute/path/new-cases \
  --native-root "$PWD/build/workload-native"
uv run --locked --extra dev --extra globus --extra roofline \
  python -m lassi_x.workload_preflight /absolute/path/new-preflight \
  --reports /absolute/path/new-cases/report.json
```

Case/preflight destinations must not exist. Preparation retains all 39 statuses,
fails on unsupported or failed workloads, and requires numerically distinguishable observable
outputs across every pair of seeds at the candidate acceptance tolerances. `--seeds` accepts at least two distinct nonnegative seeds.
The API's small-dataset override exists only for bounded adapter regression tests;
the production CLI always uses LARGE. An explicit `--workload-ids` partition
retains other workloads as unrun and cannot establish complete-cohort success.

Each kernel receives `run.yaml` with four additional `arena.correctness_tests`,
and five flat YAMLs under `cases/` for the C-adaptation pipeline's `cases` list.
Flat cases have no nested correctness suites. Every read-write input is also
an explicit output, so final mutated state is checked. Real model/toolchain
configuration is required before live translation. Use `lassi-x run CONFIG
--until cpu-verified`: the direct fixture interface does not yet support the
pipeline's downstream measurement adapters. Case-loader compatibility and C
preflight do not imply general Tenspiler frontend support.

## Native computation profiles

The manifest fixes each boundary, LARGE profile, source hash and implementation.
These are numerical kernel profiles, not reproductions of whole timed drivers.

| Suite | Native computation and LARGE profile |
| --- | --- |
| PolyBench (30) | Original kernels with `-DLARGE_DATASET`; C11, `-O2`, FP contraction off. |
| NPB CG | Original 3.4.4 Fortran `conj_grad`, all 25 iterations; class-B vector size 75000 and randomly permuted SPD CSR systems. |
| NPB MG | Original 3.4.4 Fortran multigrid, four full V-cycles; class-B 256³ interior grid and periodic boundaries. |
| NPB FT | Original 3.4.4 Fortran unnormalized positive-sign 3-D FFT; class-B 512×256×256 complex field. |
| LavaMD | Original C interactions; 1000 boxes × 100 particles. |
| Myocyte | Original float cardiac model and adaptive ODE solver; 64 cells × 100 ms, all 101 trajectory frames. |
| CFD | Original C++ flux/timestep functions, one complete three-stage RK update; 105456 conforming tetrahedra and randomized numbering. |
| ITK MI | Actual ITK join/histogram classes and entropy reductions; two 2048² images and 255² bins, replacing file I/O with memory buffers. |
| RandLAPACK | Actual RSVD/QB/RF/RS implementation and reconstruction; 2048×1024 matrix, rank 32, fixed algorithm RNG seed 42. |
| MRI-Gridding | Original Parboil `gridding_Gold`; 262144 complex samples, 128³ grid, width 3, oversampling 1.25, no LUT. |

Fortran/C++ routines are linked through typed C entry points, retaining their
actual source as context. NPB subroutine extraction omits only its program driver;
its computation is unchanged. LavaMD's missing system timer declaration is supplied
with `-include sys/time.h`. OpenMP references use a deterministic serial profile.
Myocyte initialization comes from the pinned Futhark Rodinia input linked and
hashed in `native/myocyte-initial.json`; its computation remains Rodinia's C code.

PolyBench randomizes a consumed tensor named in `RANDOM_FIELDS`, preserving native
parameters and structural state. Cholesky/LU receive SPD matrices, Durbin receives
bounded correlations, Floyd-Warshall gets positive weights with absent edges
preserved, and Nussinov gets a valid four-symbol sequence. Other tensors use fresh
uniform values. The application adapters randomize meaningful fields while retaining
domain constraints: physical Euler states and consistent tetrahedral geometry,
positive particle charges, nearby physiological ODE states, complex gridding
samples, correlated images, low-rank matrices, zero-mean periodic RHS fields,
and complex FFT fields. Seeds and workload-specific RNG streams are recorded.
Canonical typed input artifacts and hashes define the exact inputs.

Independent checks include sparse-system residuals, multigrid residual reduction,
FFT energy/DC and small full transforms, pair-force balance, ion positivity and
ODE evolution, an independent Euler RK
calculation, joint histograms/entropies, low-rank reconstruction quality, and
independent gridding scatter counts. These supplement the pinned reference; they
do not replace it. Regression tests reject finite, shape-correct wrong results
and C candidates that erase outputs.

## Rodinia backends and removal of DWT2D

The three active Rodinia workloads, LavaMD, Myocyte and CFD, each have CPU/OpenMP,
CUDA and OpenCL implementations in the pinned checkout. These checks use their
original CPU/OpenMP numerical routines. Rodinia is not CUDA-only.

DWT2D means two-dimensional discrete wavelet transform, an image-processing
operation used in compression such as JPEG2000. The pinned Rodinia suite contains
both CUDA and OpenCL DWT2D sources; its OpenCL host code includes a CPU-device
fallback. Neither implementation was executed for the historical 40-profile
validation. That run used a separate C 9/7 port, so it did not establish
upstream CUDA/OpenCL equivalence.

DWT2D has now been removed by user request. It has no active manifest entry,
fixture specification, C port, input generator, native build target or correctness
registration. No replacement was added. The original CUDA/OpenCL files remain
unchanged inside the complete Rodinia submodule. Historical 40-profile manifests
and reports are preserved; replay them at their recorded harness revision.

## C preflight and evidence

Preflight uses the existing original-versus-adapted C gate with a byte-identical
independent source copy. It compiles both, imports identical inputs, checks every
output and every input's final state, and enforces finite deterministic results,
native types, shapes, exact integer/read-only values and floating tolerances.
MG also has an unoptimized Fortran preflight with runtime bounds checking to
catch bridge aliasing that optimized code can conceal.
It is executable harness preflight, not certification of a generated candidate.

A default full preparation has at most 234 builds and 468 reference invocations;
full preflight adds at most 390 builds and 780 invocations. Each command has a
1800-second limit. There are no automatic scientific retries, model requests or
accelerator jobs. LARGE cases consume local CPU time and disk space. New source,
precision, input profile or target changes require fresh evidence.

Reports retain configuration, source, dependency, input and output hashes. Each
reference executes twice. Duplicate binary transfers are removed after successful
preparation; canonical NPZ/NPY files remain. Passed C gates retain per-field hashes,
shape/type/outcome, sources, commands and logs; their duplicate arrays are removed
with a retention index. `--retain-raw` preserves them instead. `zero-alloc.c`
clears PolyBench allocations before original initialization to define unused
upper triangles in TRMM/TRISOLV; its hash is part of that fixture profile.

For explicitly partitioned runs, `python -m lassi_x.workload_evidence PLAN.json
EVIDENCE.json` requires exactly one predeclared owner per workload and matches every
fresh C gate to the frozen typed expected outputs. The active 39-workload inventory is `benchmarks/provenance/workloads-39.json`;
historical 40-workload evidence remains under
`docs/experiments/workloads-40-large-checks-20261104/`.
Development cases are visible to repair feedback; they are not independent
holdouts, accelerator validation, or precision/performance certification.
