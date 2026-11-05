# Multiple correctness cases

The source manifest contains 40 workloads. Its `correctness` entries distinguish
executable fixture support from sources that still require an application adapter.
The 30 PolyBench workloads have explicit trusted input/output specifications here.
The other ten workloads are **not yet pipeline-ready**. An upstream self-test does
not establish candidate equivalence against supplied inputs.

## Development check plan

Scope: prepare and execute native CPU reference cases, then exercise the existing
candidate correctness-suite gate. No model requests, accelerators, or performance
measurements. Input cohort: the explicit paths and hashes in
`../provenance/workloads-40.json`; no directory discovery or pass-based selection.

Each PolyBench kernel has five independent seeded random development cases,
**all compiled with `-DLARGE_DATASET`**. Seeds default to 0, 1, 2, 3, 4 and can
be supplied explicitly with `--seeds`; at least two distinct nonnegative seeds
are required. The native initialization only bootstraps the input interface;
it is not one of the candidate's correctness cases. There is no size progression.

For each seed, the named consumed tensor in `RANDOM_FIELDS` receives fresh random
values; other native inputs, dimensions, boundary state and iteration counts stay
fixed. Most fields use uniform [0.1, 1) values. Cholesky and LU receive symmetric
strictly diagonally dominant positive definite matrices. Durbin receives bounded
correlations giving a strictly diagonally dominant unit-diagonal Toeplitz matrix.
Floyd-Warshall receives positive integer weights with absent edges preserved;
Nussinov receives random symbols in [0, 4). These are random tensors, not scalar
rescalings of native data. Seeds and per-workload streams are reproducible, and
exact input artifacts and hashes are saved. Changing NumPy versions requires
regenerating and recording the inputs with the locked environment.

Every exact input is imported into the pinned C computation to produce its own
expected output. The same input contract goes to the candidate. Every candidate
revision must pass all five cases; passing one case never establishes acceptance.

Preparation is explicit local CPU execution:

```sh
uv run --locked --extra dev --extra globus --extra roofline \
  python -m lassi_x.workload_checks /absolute/path/to/new-check-directory
```

The destination must not exist. Preparation runs at most 180 oracle builds and
360 reference invocations for the default five seeds, with 1800-second timeouts
per command and no retries. Larger seed lists scale these finite budgets to
30 × (1 + seed count) builds and twice as many invocations. LARGE references
can require substantial CPU time and disk space; this command executes them.
It records all 40 workload statuses in `report.json`, including unsupported or
failed workloads. Its exit status is nonzero until every workload is supported
and its references pass. It produces a `run.yaml` per supported kernel, with
four additional cases in `arena.correctness_tests`. Configure real models before
using these configs, and use `lassi-x run CONFIG --until cpu-verified`: the direct
fixture interface does not support downstream measurement yet.

The selected native entry points must match manifest source hashes. Reports also
record fixture specification, allocator, utility source/header, configuration,
input-contract and expected-output hashes. Each oracle uses two determinism runs,
C11, `-O2`, and disabled FP contraction. Input storage types, shapes, access
rights, scalar arguments and output order are part of the fixture contract.

`zero-alloc.c` delegates allocation to the pinned PolyBench utility and clears
storage before upstream initialization. TRMM and TRISOLV leave unused upper
triangles uninitialized. Defining these unused values makes whole-array binary
export deterministic. This allocator does not change the upstream initializers,
computational kernels, or initialized values. It is an explicit fixture profile,
and its hash belongs to the reference identity.

These are development checks, visible to correction feedback. Every candidate
revision must pass all five; primary-only output memorization fails. They are
not independent holdouts, target validation, or precision certification. The
regression tests use MINI solely to bound adapter test cost for all 30 kernels,
plus a native LARGE Durbin test. Production preparation always uses LARGE. Tests
exercise candidate rejection and correction through `validate_candidate`. No
LARGE cohort sweep or candidate/model campaign has been run by these unit tests.

## Remaining application adapters

NPB CG/MG/FT, Rodinia LavaMD/Myocyte/DWT2D/CFD, ITK mutual information,
RandLAPACK randomized SVD and Parboil MRI-Gridding require explicit computation
boundaries before their candidate interfaces can be frozen. A full benchmark and
an inner numerical kernel have different inputs and outputs. Their adapters must
retain the pinned upstream computation, supply trusted inputs to both reference
and candidate, regenerate native expected results for alternate inputs, and
configure multiple correctness cases. A placeholder or an unrelated scientific
fixture must not stand in for one of these workloads.
