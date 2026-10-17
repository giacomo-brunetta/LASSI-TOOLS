# Low-precision repair protocol

The GPU is the evaluation platform. The scientific objective is a useful implementation
that can subsequently run without explicit FP32/FP64 tensor arithmetic.

## Prompt contract

New configurations default to `compensation.arithmetic_policy: target_format_only`.
The shared contract is supplied to planners, candidate authors, accelerator compatibility
repair agents, and numerical repair agents. It requires:

- Main operators, persistent state, reductions, compensation state and outputs remain in
  the requested FP16/BF16 format. Explicit wider work and helper-internal promotion are
  forbidden. Wider implicit hardware accumulation requires explicit destination support.
- Separate FP32/FP64 validation paths remain available. Reference input initialization can
  use its documented source precision before a storage cast, but cannot precompute kernel
  work. The timing boundary and preprocessing cost must be documented.
- `forward` consumes the values actually supplied. It must not reconstruct deterministic
  fixtures, cache answers, specialize on validator inputs or read oracle values.
- The workload, output coverage and error thresholds remain fixed. An unsuccessful
  compliant attempt is a valid experimental outcome.
- Useful strategies include stable reformulation, scaling, centering, changed reduction
  structure and target-format compensation/multiword arithmetic.

`compensation.arithmetic_policy: mixed` is a separate accumulation-only arm. The backend
must explicitly allow exact operator names in `capabilities.mixed_accumulation_ops`.
The current eager auditor supports `aten.sum.default`, `aten.sum.dim_IntList`,
`aten.mm.dtype`, and `aten.bmm.dtype`. Only target-format floating inputs may enter
these operations, and any FP32 result must be cast back before subsequent arithmetic.
This does not permit wider residual/state evolution or whole-kernel promotion. An empty
allowlist permits no exception; an allowlisted operation may still be unavailable on
the device/Torch release and must actually execute successfully. Compiler-backed targets
need their own trusted qualification; an eager observation is not a compiler certificate.

Every point records `arithmetic_class`, `observed_tensor_dtypes`, `wider_operations`,
`implicit_accumulator_precision`, and the existing source/policy-bound precision verdict.
Classes are `target_only`, `mixed_accumulation`, `wider_compute`, `control`, or `unverified`.
They describe **explicit observed tensor arithmetic**. Vendor-internal accumulation remains
`unverified`; FP16 tensors alone do not prove FP16 internal accumulation. Declarations do
not certify a class. Failed policy observations are retained, not dropped.

Frontier domination and plotted frontier lines are separated by arithmetic class. Exported
frontiers include `arithmetic_tracks`; summaries keep stable-observation counts per class,
not a pooled strict/mixed success rate. FP64 and audited FP32 are controls.

The numerical agent's technique list excludes explicitly wider techniques under the
target-format-only contract. Generic skill examples cannot override this contract.

## Fixed inputs and same-kernel strategy history

Numerical repairs default to `freeze_input_builder: true` and `require_hypothesis: true`.
The harness freezes the builder AST and transitive top-level dependencies. Forward-only
changes and new imports used exclusively by forward remain possible. Edited initialization,
encoding or dimension dependencies are rejected before target measurement. Torch repair
measurements also build inputs from the authoritative baseline, record its source hash,
and run the existing FP32 supplied-input perturbation checks outside timing. These checks
are not a proof of behavior over all inputs or a hostile-code sandbox.

Before implementation, an extra bounded model turn must return a JSON hypothesis with
`technique`, `failure_mechanism`, `transformation`, `semantics_argument`, `arithmetic_plan`,
`strategy_key`, and `novelty`. Reusing a strategy key needs a specific `revisit_reason`.
Exact AST-identical implementations (ignoring comments/docstrings/precision declarations)
are rejected independently of technique labels. This does not prove that differently
written algorithms are distinct numerical strategies; the recorded hypothesis makes that
review possible. Correction rounds remain bounded and are revisions, not independent
discoveries. Rejected/no-op/invalid-plan attempts remain recorded with token usage.

History defaults to `<run>/repair-history/`; optional `compensation.history_dir` enables
sharing within a deliberately chosen experiment root. It is partitioned by kernel,
reference hashes, oracle/tolerances, datasets, repair model/provider/route/effort and
arithmetic policy. Precision is intentionally not part of this scope: FP16 and BF16
can learn from the same arm's history but are scored separately. Other models' repairs,
other kernels, other workloads and the other arithmetic arm are not injected. Generic
cross-run agent memory is disabled for numerical repair. Choose a fresh history root
for an independent repetition; do not point it at legacy or another comparison.

The workspace receives a compact `history/ledger.json`, with prior sources in
`history/*.py` available on demand. Sources and result records are retained outside the
agent workspace as immutable events. Same-arm/kernel calls are serialized within the
pipeline process so later candidates see earlier outcomes. Independently launched
processes must not simultaneously share a history root; this is not a distributed lock.

Variants retain their hypothesis, history scope, per-attempt evidence, repair-model and
policy identity, total tokens, elapsed time and tokens/time to first measured accepted
improvement. `accuracy_improved`, `error_reduction_factors`, and `recovered` distinguish
improvement from crossing the fixed 1% relative-L2 stability threshold. Revalidation-only
success without target measurements is not a measured improvement. Counts of measurements
and revisions are not independent model trials. Input-representation optimization should
be evaluated as a separate experiment, not folded into fixed-input numerical repair.

## Joint FP16/BF16 strategy

Prefer one shared source intervention for both formats and independently measure each
format against its own baseline. Scaling or a better reduction can benefit both formats.
However, FP16 has less exponent range and BF16 has fewer significand bits. A repair can
therefore fix FP16 overflow without fixing BF16 rounding, or vice versa.

For an efficient future campaign, supply evidence for both formats to one session per
base candidate, accept one dtype-generic source, then evaluate both formats. Only give
the unresolved format an additional agent session. Preserve per-format acceptance,
regression checks, latency/error measurements and a shared-session token total; do not
charge a shared repair's token cost twice or count two measurements as two independent
model discoveries.

The current pipeline still groups repair sessions by candidate and precision. Prompting
for reusable code does not implement the shared-session workflow above. Changing that
grouping and its retry/checkpoint semantics is separate work before campaign launch.

## Skill delivery

All 15 bundled skills and their auxiliary files must match the installed versions.
`skills doctor` now checks file contents rather than only skill names/frontmatter.
Pipeline startup fails when required automation skills or their auxiliary files are stale
or absent. Synchronization preserves conflicting local edits rather than overwriting them.

Workers receive full task-relevant skill instructions in their system context. Numerical
workers also receive the techniques reference in full. Other skills, references and
executable templates remain installed and available through the skills tool. No model
call is needed to verify delivery to the worker constructor.

## Acceptance is still an independent harness responsibility

Prompt instructions are not enforcement. Before launching the fresh campaign, add and
verify a dtype audit of the executed/lowered target graph, including intermediates and
helper operations. Verify supplied-input dependence with independent inputs and immutable
reference/validation artifacts. Self-declared precision metadata and passing one fixture
are insufficient. Source grep alone cannot prove target-format-only execution.

No fresh campaign should be described as compliant until those checks exist. GPU
compliance also does not establish compiler compatibility or runtime behavior on the
eventual accelerator; those require direct testing there.
