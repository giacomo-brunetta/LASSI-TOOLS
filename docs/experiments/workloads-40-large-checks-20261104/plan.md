# Forty-workload LARGE random-input correctness plan

## Question and scope

Establish native-reference preflight and multiple meaningful random-input
correctness cases for every one of the 40 explicitly listed workloads. User
requires LARGE directly, with no size progression. Five independent seeds 0–4
per workload. No model calls, accelerators, or timing claims. Interface:
trusted native computation through C fixture entry points, followed by the
existing candidate suite gate. Source languages remain part of provenance.

## Reproducible environment

Harness starting commit: a067a21fc39d271b7b67a59d8a27ea04b47e7fb2.
Host: macOS-26.6.2-arm64-arm-64bit-Mach-O. Python: 3.13.13.
Lock SHA256: bc6ad886757eb3abe04f699af6bdc224d5b5e0f13e6bf89e507f4ba0470c3b4a.
Native C compiler: system cc, C11, -O2, -ffp-contract=off. Install missing local
CMake/Fortran/OpenMP tools to compile the actual pinned libraries and reference
routines. Record build commands and tool identities in each output. Preserve
submodule commits; do not edit their source trees. No credentials are needed.

## Complete cohort and artifact identities

Manifest: /Users/giacomobrunetta/Projects/LASSI-TOOLS/benchmarks/provenance/workloads-40.json
Starting SHA256: 59e59ecfb226d507fb245450f5b496ac40fe5989506eddca1b7cf7f62d56e3ff.
All 40 entries remain in denominators. Original source hashes are mandatory;
adapter, dependencies, cases and generated artifact hashes are recorded.
Artifact root: /Users/giacomobrunetta/Projects/LASSI-TOOLS-artifacts/workloads-40-large-20261104. First PolyBench pass: /Users/giacomobrunetta/Projects/LASSI-TOOLS-artifacts/workloads-40-large-20261104/polybench-v1.
New adapters have named computation boundaries and explicit LARGE profiles;
there is no universal cross-suite LARGE macro. Native C++/Fortran implementations
may be linked through C interfaces, with their source dependencies supplied as
context. Any C port must be labelled and independently checked; an unrelated
fixture cannot replace the requested suite.

## Reference and candidate interface

30 PolyBench fixture specifications live in benchmarks/checks. Five random
cases use unchanged LARGE dimensions and native structural state. For remaining
10, freeze inputs, dimensions, all observable outputs and random validity rules
before execution. Import exact values to both reference and candidate. Protect
read-only inputs, compare all read-write state, and repeat changed-source gates.
Reference expected results must be deterministic and finite over two runs.

## Gates and outcomes

Every workload must compile and run all five native seeded cases. Inputs must
retain exact shapes/types and valid application domains; cases must differ in
consumed values, produce informative outputs, and exercise application-specific
invariants. Candidate suite regressions must reject memorized/incorrect results
and accept a correct implementation for every case. C preflight means executed
native build/import/export and repeatable finite expected outputs, not syntax
checking alone. Native language and portability limitations stay explicit.
No accelerator, performance, or independent holdout claims are made.

## Finite budgets and resource ownership

Five cases plus at most one native-interface bootstrap per workload. At most
240 builds and 480 native invocations for one complete 40-workload pass.
1800-second command timeouts, no automatic scientific retries; named revised
passes retain preceding outcomes. Initial PolyBench pass wall limit 7200s.
Local reference preparations run sequentially; dependency builds may use four
CPU jobs. No model sessions/costs, accelerator jobs, or remote workers.
Record process sessions in the launch record; cancellation preserves partial
reports and marks unrun cases incomplete. Additional adapter development and
checks remain bounded per explicit command/test invocation.

## Commands and launch record

Locked invocation prefix: uv run --locked --extra dev --extra globus --extra roofline.
Launch first PolyBench reference pass using prepare(root, polybench-v1) with
an asyncio 7200-second overall timeout. Evidence remains external at the root
above. Update this plan and the evidence index with subsequent exact commands.

## Results and denominators

Planned: 40 workloads × five seeded LARGE cases = 200 candidate cases.
Starting support: 30 PolyBench adapters; ten missing. Starting executed LARGE
evidence: Durbin five cases in unit tests. No full LARGE cohort claim yet.
All build failures, numerical failures, interrupted and unsupported cases remain
visible in report inventories. Retrying requires a distinct output destination.

## Handoff

Current stage: executing preparation and adapter development. Model and hardware
budgets remain zero. Unrelated compatibility documentation and historical
untracked artifacts must remain untouched. Development cases are visible to
repair feedback, not holdouts. Full repository quality checks and exact pushed
commit CI must pass before final completion.

## Extended preflight phase and launch record

The explicit continued goal includes C preflight for all 40 workloads. After the
reference preparation phase, execute the existing `c_to_torch.c_gate` for all five
cases per workload using a byte-identical independent source copy. This phase
has an additional finite budget of 400 builds and 800 executions, command timeout
1800s and overall wall limit 7200s per declared partition. It verifies every
observable output plus final state of every input, including exact read-only
preservation, shape, type, deterministic finite results and configured floating
comparison. It is original-versus-same-source harness preflight, not evidence
about any model-produced adaptation or accelerator.

Explicit partitions, declared by suite membership (never by outcome):

- PolyBench 30: preparation `polybench-v1/report.json`, preflight
  `polybench-c-preflight-v1/report.json` beneath the artifact root above.
- Native 10: preparation `native-large-v1/report.json`, preflight
  `native-c-preflight-v1/report.json` beneath the same root.

Preparation scripts `launch-polybench.py` and `native-large-v1.py`, and preflight
scripts `polybench-c-preflight-v1.py` and `native-c-preflight-v1.py` record the exact
calls. Their `.log` counterparts preserve progress and errors. Earlier native
small-adapter development passes remain separately in `native-small-v1` and
`native-small-v2`, with independent checks in `small-invariants.log`; these do not
replace LARGE evidence. A first upstream RandLAPACK installer build reached its
optional upstream GoogleTest discovery but failed due a missing conda gtest
runtime path. The workload library was installed with those unrelated upstream
tests disabled, and its actual RSVD computation is separately executed by this
cohort. No failure is counted as a passing workload test.

Canonical NPZ inputs/outputs and expected NPY results are retained. After a
successful case, duplicate binary import/export buffers may be removed with a
retention index. C gate field hashes, shapes, dtypes, logs, commands and sources
remain. Final evidence must compare every gate's original-output hashes against
the corresponding frozen preparation outputs, and retain all declared IDs.

Native reproducibility adds pinned BLAS++, LAPACK++ and Random123 submodules.
`tools/prepare_workload_dependencies.py` builds ITK and RandLAPACK from those
pins under the explicit `native-deps-repro` artifact root, with a command and
library-hash inventory. No source downloads happen in that helper. The local
Fortran/CMake/OpenMP tools were installed with Homebrew; their actual versions
belong to the final environment inventory. The ten native computation boundaries
and LARGE profiles are fixed in `benchmarks/provenance/workloads-40.json`.
DWT uses a documented serial C port of the pinned CUDA lifting algorithm, with
independent coefficient and reconstruction checks; no CUDA hardware equivalence
claim is made. NPB invokes the original 3.4.4 Fortran routines through C entry
points; CFD invokes the original C++ flux/step functions for one complete RK
update. These boundaries are scientific kernel profiles, not full timed driver
reproductions.

## Complete mutable-state profile revision

The C-adaptation case loader requires every read-write input to be an explicit
output. Eight initial PolyBench specifications omitted final mutated arrays:
correlation, covariance, gemver, gramschmidt, heat-3d, jacobi-1d, jacobi-2d and
ludcmp. This predeclared interface-based partition receives fresh preparation
and preflight under `polybench-state-v2` and `polybench-state-c-preflight-v2`.
The other 22 PolyBench workloads retain their unchanged v1 profiles; native ten
retain their unchanged LARGE v1 profiles. No outcome-based selection occurs.

Additional finite revision budget: 48 builds/96 executions for eight reference
preparations and 80 builds/160 executions for eight five-case C gates; 1800s
command limits, 7200s wall cap per phase, no automatic retries. Preserve v1
evidence as earlier profiles. Final partitions explicitly own 22 + 8 + 10 IDs.
Every supported workload also exports five flat case YAMLs (no nested suites),
so `c_to_torch` can load them directly without weakening its existing checks.

## CFD normal convention and boundary coverage revision

The native CFD driver negates mesh-file normals before its numerical routines.
The final random mesh profile explicitly supplies this inward convention and
adds transverse slip walls alongside x inlet/outlet far-field faces. All three
neighbor branches are required. CFD alone receives fresh `cfd-profile-v2`
preparation and `cfd-profile-c-preflight-v2` evidence; the other nine native
profiles are unchanged. Additional finite budget: six reference builds/twelve
executions plus ten C-gate builds/twenty executions, with existing command and
phase wall limits. Final partitions own exactly 22 + 8 + 9 + 1 workloads by
these predeclared interface/profile changes, never by observed success.

## DWT source-identity formatting revision

Remove four trailing spaces in the copied DWT copyright comment before commit.
This changes the full-file reference hash without changing computation. DWT
alone receives fresh `dwt-source-v2` preparation and `dwt-source-c-preflight-v2`
evidence (six plus ten builds, twelve plus twenty invocations, unchanged finite
command and phase limits). Final predeclared ownership is 22 unchanged PolyBench
+ eight mutable-state PolyBench + eight unchanged native + CFD + DWT.

## MG bridge alias correction

Use a local loop counter as the final `mg3P` argument, matching the original
NASA driver, rather than aliasing the module hierarchy-depth variable `lt` that
`mg3P` reads while modifying its counter. The original Fortran routines remain
unchanged. MG alone receives fresh `mg-bridge-v2` preparation and
`mg-bridge-c-preflight-v2` evidence: six plus ten builds, twelve plus twenty
invocations, with unchanged command/phase limits. Its partition is removed from
the unchanged-native partition before execution, independent of outcome.

## Numerical discrimination and MG debug regression

Require every pair of seeded reference outputs to differ beyond the configured
candidate acceptance tolerances, rather than relying only on different byte
hashes. A real-reference negative test supplies sub-tolerance perturbations and
must fail preparation. The final frozen-output audit enforces this criterion
across all 200 LARGE cases. Add an MG C preflight with Fortran `-O0 -fcheck=all`
to expose hierarchy-counter aliasing that optimized Fortran can conceal. This
is a bounded development regression (two builds/four executions on the small
profile), separate from final LARGE evidence. Production compile flags stay
unchanged.
