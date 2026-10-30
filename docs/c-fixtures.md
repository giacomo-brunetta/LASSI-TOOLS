# Inputs supplied by the correctness harness

Set `oracle.fixture_spec` to a trusted YAML specification to use executed C inputs
for correctness acceptance. The configured build command must compile the desired
dataset, for example `-DLARGE_DATASET`, and support C11 generic selection. The
harness preserves the original include directory and compiler flags. It never
translates initializer expressions into Python.

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
