# Inputs supplied by the correctness harness

Set `oracle.fixture_spec` to a trusted YAML specification to use executed C inputs
for correctness acceptance. The configured build command must compile the desired
dataset, for example `-DLARGE_DATASET`, and support C11 generic selection. The
harness preserves the original include directory and compiler flags. It never
translates initializer expressions into Python.

## Original source preservation and generated instrumentation

The original file containing the kernel is a read-only reference. Never insert
fixture hooks, initialization changes, computation anchors, or output dumps into
that file, and never apply instrumentation patches inside a benchmark submodule.
Keep generated run/build artifacts outside those source submodules. Source
changes that are intentionally being evaluated belong in separate candidate or
adapter files, with their own identity and validation evidence.

`build_fixture_oracle` reads the reference and writes an instrumented copy to
`<run_dir>/oracle/c-fixture/reference.c`. The configured `{reference}` build
placeholder resolves to this generated copy. Instrumentation adds binary input
import/export immediately before the declared computation and output export
immediately afterward. The kernel body and arithmetic are retained. The original
source file is never opened for writing. If explicit computation anchors are
needed, provide them in a separate fixture entry point instead of editing the
upstream kernel file.

The active workload adapters live separately under
[`benchmarks/checks/native`](../benchmarks/checks/native/). C++/Fortran bridges
call the pinned native routines. NPB's extracted `routines.f90` and generated
parameter headers are written under the artifact's `native-build` directory;
the original `.f90` files remain unchanged. DWT2D and its separate C port have
been removed from the active cohort; original Rodinia CUDA/OpenCL sources remain
untouched. The PolyBench zeroing allocator is also a separate harness file; it
defines unused storage before native initialization without editing upstream
allocation or kernel source. These distinctions and the exact workload profiles
are documented in the [workload check guide](../benchmarks/checks/README.md).

Retain the pinned submodule commit and original source SHA256 alongside the
fixture specification, generated source/build commands, input and output
identities. The cohort preparer checks the original source hashes before use;
preflight rechecks them. A mismatch must stop validation rather than silently
accept a modified original as the reference.

For PolyBench GEMM, a specification is:

```yaml
inputs:
  A: {argument: a, access: read_only}
  B: {argument: b, access: read_only}
  C: {argument: c, access: read_write}
  alpha: {argument: alpha, access: read_only}
  beta: {argument: beta, access: read_only}
  ni: {argument: ni, access: read_only, scalar: true}
  nj: {argument: nj, access: read_only, scalar: true}
  nk: {argument: nk, access: read_only, scalar: true}
outputs: [C]
```

Array dimensions come from the regular PolyBench declarations; types and sizes
come from compiled C. Argument names, access rights, scalars, and output order
are explicit. Scalars default to zero-dimensional tensors; `scalar: true` passes
a Python number, useful for loop counts. Every parameter and iteration count used
by a candidate must be included in the specification. Scratch arrays that C does
not initialize must stay internal to the computation, rather than be exported
as inputs. Only contiguous arrays and supported C floating/integer types are
exported; plain C `char` follows the compiler's signedness.

For other C references, declare unique literal `before` and `after` anchors that
enclose the computation, plus explicit C field expressions and dimensions:

```yaml
before: '  /* COMPUTE */'
after: '  /* FINISH */'
fields:
  state: {expression: state, shape: [N, '3']}
inputs:
  state: {argument: state, access: read_write}
  steps: {argument: steps, access: read_only, scalar: true}
outputs: [state]
```

The instrumented executable initializes normally, imports alternate values if
configured, exports inputs, runs the original computation, and exports outputs.
Binary transport preserves shapes and declared storage types, including integers
larger than 2^53. Inputs and outputs are checked over the configured determinism
runs. The oracle directory retains typed NPZ files, generated C, build/run logs,
and a manifest with source, specification and artifact hashes. Each fixture also
contains a checksum of its metadata and typed arrays, verified when loaded.
These checks detect accidental changes, not malicious rewriting of trusted files.

The candidate may expose a module-level `forward(a, b, c, ...)` or
`make_model()` returning a module with that forward interface. The harness calls
it with the exact named arguments; `build_inputs()` is never called for this
fixture format. Each invocation receives fresh copies. Floating arrays undergo
one conversion from their initialized C storage type to the requested Torch
dtype/device; integers retain their storage dtype. Read-only tensor mutations
fail acceptance. Return tensors in the specification's output order, including
the final value of any in-place result.

For alternate valid tests, save an NPZ input contract with `save_contract()` and
set that case's `oracle.input_fixture`. Include exactly every specified input,
using its original native dtype and shape. C verifies the binary headers and
lengths before importing values at the initialization boundary. This runs the
same C algorithm on the same alternate inputs; it does not reuse default expected
outputs. Validity constraints such as positive-definite matrices remain the test
author's responsibility. An `arena.correctness_tests` case with `fixture_spec`
does not need a separately configured `input_contract`.

This interface is integrated into correctness validation and direct candidate
execution at the requested device/dtype. Historical fixtures and their parity
checks remain supported. Existing accelerator compiler, precision-audit and
measurement workers still use the historical builder interface; they have not
been migrated to this fixture protocol. Existing benchmark campaigns also need
explicit per-kernel specifications before adopting it.
