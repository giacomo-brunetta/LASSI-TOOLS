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

`compensation.arithmetic_policy: mixed` permits selective wider arithmetic when the backend
supports it. Full-kernel promotion remains a fallback baseline rather than a numerical
repair. Compare mixed candidates with the existing FP32 accuracy/latency point.

The numerical agent's technique list excludes explicitly wider techniques under the
target-format-only contract. Generic skill examples cannot override this contract.

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
