# C input parity gate

Verification and precision measurements check the actual arguments supplied to `forward` against
an independent capture of the original C initialization. This requires no LLM
calls and does not regenerate or repair a candidate.

New campaigns prepared by `experiments/cpu-generation/suite.py` enable the check.
Existing configurations retain their original behavior. To enable it explicitly:

```yaml
arena:
  input_check:
    enabled: true
    rtol: 1.0e-12
    atol: 1.0e-14
```

When enabled, the check runs on every candidate validation, every precision
measurement, every FP32 repair-collapse check, and every subsequent repair
evaluation. Resumed runs also enforce it. A successful FP64 check or an earlier
repair attempt cannot substitute for a fresh snapshot at another precision.

## Authoritative values

`lassi_x.c_inputs` instruments a copy of the original C source immediately before
the computational kernel, or at an explicit initialization boundary in the eight
scientific programs with inline computation. It runs the C initialization using
the configured compiler, profile/type flags, and headers. It does not run the
kernel to produce expected inputs. Shapes come from C variables/macros rather
than a duplicate Python size table. Deriche's native FP32 initialization is
preserved even though the Torch verification request is FP64.

The capture covers the main campaign's 33 applications. A regression test also
compiles and captures all 39 applications in the extended suite. Unknown source
layouts and external input fixtures require an adapter and fail explicitly.

C workspaces that are uninitialized and written before use are represented by
zeros, without reading uninitialized memory. The unused, uninitialized upper
triangles of TRMM and TRISOLV are also represented by zeros. Candidates should
omit unused workspace arguments or zero-initialize them. If a workspace is
supplied, its checked values must match the contract. In contrast, arrays
initialized as part of C input construction, including LU/Cholesky Gram matrices
and Poisson's initial residual norm, retain their original initialized values.

## Matching the candidate interface

Every supplied positional argument is checked. Named forward parameters bind to
C variable names, allowing case differences, underscore differences, and common
`_in`, `_input`, and initial-value suffixes. A small set of explicit legacy aliases
is defined in the harness. Singleton batch/channel dimensions are allowed;
arbitrary broadcasting, flattening, or permutations are not inferred.

The harness also defines the existing GESUMMV `M = stack(A, B)` and doitgen
`weight = C4.T` interfaces. Other representations need a reviewed harness binding:

```yaml
arena:
  input_check:
    enabled: true
    bindings:
      matrix: A
      weight: C4.T
```

These example bindings belong to different kernels; configure only those needed
for the selected kernel. Legacy variadic forwards use positional keys such as
`"#0": A`. Candidate-authored metadata never determines expected values or binding
rules. Unknown arguments fail, even if another argument already matches the C
data. Required independent data arrays must be present; constants embedded in
the algorithm and optional scratch arguments may be absent.

FP64 floating values use the input-specific tolerances above. For FP32, FP16, and
BF16, the authoritative C-initialized values are converted **once** to the
requested storage format, and supplied values must match that rounded result
exactly. Builders should initialize in high precision and cast once, rather than
perform initialization arithmetic in the target format. BF16 snapshots use a
lossless widening because NumPy has no native BF16 type. Integer-valued fields
retain their original values and all-zero workspaces are exact. The check rejects missing data,
unknown arguments, nonfinite values, shape differences, and value differences.

A target cast that produces Inf is an input-representability failure; it is not
evidence of cheating. Similarly, a mismatch can expose different initialization
rounding rather than an incorrect forward algorithm.

The measurement capture uses the actual evaluation dataset. Standard PolyBench
profiles select their corresponding C dataset macro and cache a separate C
capture. Custom profiles can provide a trusted archive through
`arena.input_check.contracts`, keyed by dataset name. A MINI input capture is
never silently used to validate a LARGE workload.

## Execution and evidence

The runner snapshots the supplied arguments after model construction and before
forward execution. A worker check rejects mismatches before forward. The harness
retrieves the snapshot and independently repeats the comparison against its own
contract before accepting the candidate. Modifying the worker's fixture or
claiming success in a worker report cannot override this comparison.

Artifacts include:

- `oracle/input-contract/inputs.npz`: authoritative C inputs and metadata.
- `oracle/input-contract/capture.c`, build command and logs: C capture provenance.
- `fp64.inputs.npz`: actual pre-forward argument snapshot.
- `fp64.inputs.json`: harness-side input decisions and bounded mismatch details.
- `<variant>-<precision>-inputs.json` and `.npz`: measurement input evidence.

Each new measurement includes an `input_check` record containing its protocol,
precision, dataset, source hash, and the input decision. Successful checks also
record contract and snapshot hashes. Input construction, snapshots, checks, and
transfers are outside the timing region. Input-check failure makes the cell
unsuccessful and removes its accepted latency.

Input mismatches produce a diagnostic with `gate="inputs"` for the existing repair
flow. They do not become output-equivalence failures.

Torch workers, including CUDA workers, check the actual evaluated tuple before
warmup. The executed-dtype wrapper is unwrapped for argument-name binding only;
the original input values are retained. Repair-baseline semantic probes check
the baseline's FP32 initialization and the repair's target-format initialization
before applying their deliberately perturbed test inputs. The repair-policy
checkout retains its frozen-builder and mixed-arithmetic policies in addition to
these C input checks.

Staged Graphcore and GroqFlow workers perform the same check before export or
compilation. GroqFlow's FP32 tracing tensors contain exactly the checked FP16
values. Legacy queue executors and custom native workers must implement the
snapshot protocol: when checking is enabled, missing evidence prevents a success
claim. SDK environments receive the check code alongside the worker; an old
installed harness package cannot silently skip it. Actual accelerator execution
requires the relevant hardware/toolchain and is not established by CPU tests.

To check retained accepted candidates without executing their forwards:

```sh
.venv/bin/python experiments/holdout-validation/check_saved_inputs.py \
  --snapshot docs/experiments/input-integrity-audit-20261020/main_campaign_sources.json \
  --output docs/experiments/input-parity-check-20261020
```

This records source hashes and separate results; it never rewrites the original
campaign or its acceptance counts. The script's `--one-per-kernel` option is a
coverage smoke check rather than a complete candidate audit.

## Scope

Passing establishes supplied-input agreement with the configured C fixture
within the stated input tolerances. It does not establish algorithmic correctness,
verify constants or results hidden in model state, demonstrate that forward uses
its arguments, or provide isolation against adversarial Python monkeypatching.
An implementation can supply correct inputs and still ignore them or implement
the wrong algorithm. Source review and alternate-input differential tests address
those separate issues. Historical observations without input evidence remain
historical observations; this change does not retrospectively certify or rewrite them.
