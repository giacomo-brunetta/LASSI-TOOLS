# Preparing C kernels for Tenspiler

For the full account of the installation patches, source transformations,
extended compiler/runtime, verification audit, and validation methodology, see
[Making Tenspiler work with the PolyBench kernels](tenspiler-engineering-report.md).

`python -m lassi_x.tenspiler_prepare` parses C with Clang and emits a deterministic
Tenspiler input directory. Preparation makes no model calls, changes no original
sources, and runs no solvers. Clang and the locked framework environment are needed.
Tenspiler execution uses its separately installed Python/LLVM/Racket environment.

```sh
.venv/bin/python -m lassi_x.tenspiler_prepare \
  benchmarks/polybench/linear-algebra/kernels/gemm/gemm.c \
  --include benchmarks/polybench/utilities --define LARGE_DATASET \
  --integer-model --extended --output runs/prepared-gemm
```

Repeat `--include` and `--define` for the exact compilation context. `--function`
selects a function other than a single `kernel_*` definition; `--clang` selects the
parser. Existing destinations are refused. Identical inputs/options emit identical
bytes. The manifest records source/header hashes, generated hashes, interfaces,
transformations, and arithmetic/proof scope. Unsupported syntax is rejected before
creating the destination.

## Two preparation paths

The direct path recognizes matrix–vector reductions, including transposed accesses,
independent/dependent stages, either product operand order, and initial accumulator
vectors. It emits original-type C++ reference stages, explicit vector returns and
an integer model when requested. Nonzero accumulators remain interface inputs.
Only positive logical dimensions, rectangular matrices and disjoint arrays are
supported; the reference wrapper checks shapes. ATAX, BiCG and MVT use this path
by structure, without kernel-name dispatch.

Explicit `--extended --integer-model` also permits composed operators. A normalized
Clang AST describes the original computation, with dependence checks controlling
parallel loop distribution and reduction lifting. Supported patterns include scalar
coefficients, matrix outputs, triangular bounds, local scratch, branches, scalar
math, guarded min-plus pivots, point-stencil wavefronts, and interval recurrences.
Tenspiler generates primitive/stage Torch functions; deterministic orchestration
implements indexing, shapes, loop schedules and tensor control. This is **composed
operator generation, not whole-kernel Tenspiler synthesis or verification**.
The runtime rejects unsupported aliasing, ragged loops and excessive intermediate
materialization rather than silently dropping work.

Ordinary composed reductions may reassociate floating additions or distribute sums.
`--ordered-reductions` selects composed execution and preserves per-output scalar
accumulation order. This can resolve sensitive recurrences such as Durbin and
Gram–Schmidt, with a performance cost. It does not remove the need for validation.
Positive constant-base `pow` is normalized through `exp(log(base)*exponent)`;
this mathematical normalization also requires floating-point checks.

Residual sequential loops default to a 100,000-iteration budget, configurable with
`--scalar-step-limit`. Ordered reductions and wavefront schedules each have a
4-million-step cap; materialized intermediates are capped at 16 million elements.
Budget exhaustion is an incomplete execution, not evidence that the C is impossible
to translate. This is a restricted C adapter, not a general C compiler.

## Synthesis and proof boundaries

Converting floating arithmetic to an integer model changes semantics. An integer
proof never establishes FP32/FP64 equivalence. Integer sqrt/exp models are upstream
abstractions, not floating implementations. Validate every generated kernel against
independently compiled original C using identical typed inputs and dataset flags.

```sh
source runs/tenspiler-native-20261103/activate.sh
python runs/prepared-gemm/synthesize.py \
  --tenspiler-root "$PWD/runs/tenspiler-native-20261103/source" \
  --llvm-bin "$PWD/runs/tenspiler-native-20261103/llvm11/bin" \
  --llvm-pass "$PWD/runs/tenspiler-native-20261103/llvm-pass-build/addEmptyBlocks/libAddEmptyBlocksPass.so"
```

This machine's installation uses native arm64 Python 3.9, Torch 2.1.2, LLVM 11,
Racket, Bitwuzla and CVC5. Other installations can supply their own absolute paths;
`--sysroot` defaults to `SDKROOT`. The tool first checks prepared-file hashes, then
compiles and synthesizes. Defaults: symbolic bound 2 and 30 seconds per stage/operator;
compilation has separate 30-second limits. `--bound`, `--timeout` and a new
`--run-dir` select explicitly budgeted attempts. Timeout cleanup terminates the
synthesis process group; failed attempts retain logs and `status.json`.

Unbounded verification is requested by default. `--bounded-only` explicitly skips
it and emits candidates from bounded synthesis. Status records distinguish this
policy, and its candidates require independent numerical qualification. Composed
runs accept an optional `--operator-cache DIRECTORY`; keys include model source,
driver templates, native source identity, compiler identity, symbolic bound and
verification policy. Bounded results cannot satisfy an unbounded cache request.

The local driver corrects two defects found in the pinned upstream verifier:
empty-prefix elementwise/matrix axioms, and a missing empty-column base case in
the SMT transpose definition. The submodule stays unchanged; unknown SMT prelude
layouts fail closed. Forward matrix–vector proofs can succeed with corrected
assumptions, while transposed and biased stage proofs remain unresolved within
the recorded budget. Earlier solver UNSAT records made with the defective
assumptions must not be treated as trustworthy formal proofs. Historical
numerical C comparisons remain separate evidence.

## Generated interface and qualification

Direct preparation emits `kernel.reference.cc`, original-type stage sources,
optional integer sources, `synthesize.py`, `README.md` and `manifest.json`.
Composed preparation emits `kernel.original.c`, `program.json`, integer operator
sources, synthesis/stage drivers, `runtime.py`, a README and the manifest.
Both emit `synthesis/kernel_torch.py` after successful synthesis.

`kernel_torch.forward(...)` accepts arguments in manifest `program.inputs` order
and returns a tuple in `program.outputs` order. Composed interfaces preserve all
original parameters, including scalar dimensions. Mutated arrays are cloned;
all mutated outputs, including scratch and boundaries, require comparison.
Generated stage functions preserve supplied tensor dtypes; upstream convenience
wrappers that force FP32 are not used. Scalar conditional codegen receives a
deterministic tensor-control AST postpass, with raw generated code preserved.

No emitted candidate is automatically validated or benchmarked. Qualification
must record the original C initializer/alternate-input protocol, source and input
hashes, shapes, precision, finite-output policy and numerical thresholds. A
nonfinite original-C case is a reference failure, not a candidate pass. Development
feedback and numerical qualification do not constitute an independent final holdout.

The local, uncommitted archive at
`docs/experiments/tenspiler-expanded-20261104/RESULTS.md` records the fixed 30-kernel MINI/LARGE cohort, retained failed attempts, proof audit,
and compiler-generated baseline catalog. All transformations and subsequent
synthesis runs use zero LLM-service calls.

For LLM-proposed minimal C edits with separate original-C and Torch gates, see
[C adaptation followed by Tenspiler](c-to-torch.md).
