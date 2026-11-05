# Forty-workload LARGE random-input checks

**40/40 workload profiles and 200/200 random LARGE cases passed native reference
preparation, C preflight, and the frozen-output evidence audit.** Seeds are 0–4;
dimensions stay LARGE throughout. All five cases produce distinct observable
outputs for each workload, distinguishable beyond the acceptance tolerance
for every pair of seeds.

The final audit regenerated every input with the current generator and matched
its exact typed values. Fresh C preflight outputs match the frozen reference
arrays, including shape and native dtype. C gates also check all inputs' final
state and enforce read-only preservation. Every read-write input is an explicit
output. All 200 flat YAML cases load through the C-adaptation pipeline's actual
case loader.

Local repository checks passed: lint, formatting, strict types and **677 tests
passed, 3 availability skips**. The native workload tests are required and do not
silently skip absent dependencies. The dependency preparation helper was built
and exercised from the pinned submodules. The MG bridge uses a separate cycle counter and passes an unoptimized Fortran
runtime-bounds-checking C preflight. Sub-tolerance input changes are rejected
by a real-reference negative test. Final DWT copyright-comment whitespace
cleanup received its own fresh five-case LARGE preparation and C preflight.

- [Audited case outcomes and hashes](evidence.json)
- [Explicit executable case configurations](cases.json)
- [Environment and library identities](environment.json)
- [Predeclared cohort partitions](partitions.json)
- [Experiment plan and validation revisions](plan.md)
- [Fixture preparation and computation boundaries](../../../benchmarks/checks/README.md)

Canonical input/output NPZs, expected NPY files, compiled-source records and gate
logs remain at the explicit external paths in these inventories. Duplicate raw
binary transfers were removed only after successful cases, with retention indexes.
Earlier development failures and superseded profiles remain separate artifacts.

These are executed native-reference and C-harness checks, plus pipeline case-loader
compatibility. They do not certify generated Torch, general Tenspiler frontend
support, accelerator execution, independent holdouts or performance. NPB uses its
original 3.4.4 Fortran routines through C entry points; ITK/RandLAPACK/CFD retain
their native C++ computations. DWT uses the documented serial C port of the pinned
CUDA lifting algorithm, with independent coefficient/roundtrip checks; CUDA
hardware equivalence was not evaluated. No models or accelerators were contacted.


## DWT interpretation

The 40-profile count includes the separate serial C DWT 9/7 port. It does not
establish equivalence to the original Rodinia CUDA or OpenCL implementations.
Both are present and unchanged in the pinned repository; neither was executed
for this validation. DWT's LARGE cases check reconstruction, while bounded small
cases additionally check coefficients against independent lifting equations.
See the [backend and DWT explanation](../../../benchmarks/checks/README.md#rodinia-backends-and-removal-of-dwt2d).


## Subsequent cohort change

DWT2D was later removed by user request. This report remains a historical record
of the 40-profile run, including its explicitly labelled C port. The active
cohort is now [39 workloads](../../../benchmarks/provenance/workloads-39.json),
with five LARGE cases each (195 cases). The former DWT C port is no longer an
active reference. Original benchmark files remain unchanged.
