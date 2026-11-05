# Deterministic Torch expression repair with Herbie

`python -m lassi_x.herbie` prepares a restricted PyTorch `forward` as FPCore,
runs Herbie with a fixed seed and finite deadline, and translates the resulting
expression back into a Torch module. It uses no language model. The output is
**`proposal.py`, requiring independent validation**. This adapter does not change
the default compensation worker or automatically accept a phase 2 repair.

## Supported contract

Select one stateless class inheriting directly from `torch.nn.Module`, with only
a `forward` method. Its positional arguments must all be floating tensors of
the same declared base dtype and device. The supported forward consists of
single assignments and one tensor return. Every argument must contribute to
the returned expression, so the adapter can preserve the output's broadcast
shape even when Herbie eliminates an argument or returns a constant.

Supported source expressions are `+`, `-`, `*`, `/`, unary signs, finite numeric
literals, explicit `.to(torch.float16/float32/float64/bfloat16)` casts, and the
unary Torch functions listed in `UNARY` in
[the implementation](../lassi_x/herbie.py). Combining tensors in different
precisions requires explicit casts. Constant-only Python arithmetic is refused.
FP16/BF16 tensor/scalar arithmetic additionally requires the scalar to be exactly
representable, because Torch's scalar opmath rules differ from FPCore's literal
rounding rules. Imports must use the spelling `import torch`.

Reductions, matrix products, loops, mutation, state access, helper calls, argument
defaults, conditionals, and tuple outputs are currently unsupported. The adapter
refuses them before creating an output directory. It optimizes the complete
supported forward; it does not yet extract regions from a larger unsupported
forward. Autograd behavior and alias identity are outside this inference contract.

Preparation parses source without importing it. It preserves the original module
and emits FPCore with explicit inclusive, finite ranges supplied for every input.
Ranges describe the permitted workload domain; they must come from its contract,
not oracle outputs or a final holdout. Generated code does not enforce ranges at
runtime. Its use requires a workload known to satisfy those ranges.

## Precision and platform selection

FP32/FP64 default to Herbie's `herbie20` platform. This supports expressions and
casts, but its costs and elementary functions do not model a Torch accelerator.
Unsupported results, including FMA and conditional expressions, fail explicitly;
the adapter never substitutes unfused arithmetic for FMA. Regime inference is
disabled to avoid introducing conditional tensor evaluation.

FP16/BF16 preparation requires an explicit platform. The bundled
[`herbie-fp16.rkt`](../lassi_x/resources/herbie-fp16.rkt) is an experimental,
self-contained FP16/FP32 platform for arithmetic, negation and casts. It implements
IEEE round-to-nearest-even with subnormals. It supplies no elementary functions,
FMA, branches, reductions or BF16 representation. Its wider arithmetic has a
larger **heuristic cost**, not a measured hardware latency. Copying an arbitrary
custom platform requires it to be self-contained; relative helper imports are
not copied.

For FP16/BF16, execution enables `setup:rival2`: the pinned Herbie revision's
default Rival 3 shim only supports FP32/FP64 representations. This changes the
real-expression evaluation backend, not the requested arithmetic precision.
The pinned Herbie submodule is not patched.

Generated tensor code explicitly casts each arithmetic result to its FPCore
precision. It preserves sharing in Herbie `let`/`let*` expressions and uses
broadcast tensor constants when arguments are eliminated. The optimized branch
is used only for the declared input dtype and common device; other dtype paths
run the original forward. Thus an FP16 proposal retains its original FP32/FP64
controls. Actual executed precision still needs a graph audit.

## Prepare and execute separately

The reusable example is synthetic arithmetic, not a C-qualified benchmark.
From the repository root, preparation runs entirely locally:

```sh
uv run --locked --extra dev --extra globus --extra roofline \
  python -m lassi_x.herbie prepare \
  experiments/herbie-example/candidate.py runs/herbie-example \
  --class-name Difference --domains experiments/herbie-example/domains.json \
  --precision binary16 --platform lassi_x/resources/herbie-fp16.rkt
```

Install the pinned Herbie into a separate Racket package home, using an installed
Racket executable. The installation downloads dependencies and is separate from
the locked Python environment. Preserve the resolved Racket package inventory
alongside results; installing the pinned source alone does not pin its transitive
dependencies. The adapter does not install tools automatically.

```sh
export PLTUSERHOME="$PWD/runs/herbie-native/racket-user"
/absolute/path/to/raco pkg install --auto --no-docs --name herbie \
  "$PWD/third_party/herbie/src"
/absolute/path/to/raco pkg show --all > "$PWD/runs/herbie-native/packages.txt"

uv run --locked --extra dev --extra globus --extra roofline \
  python -m lassi_x.herbie optimize runs/herbie-example \
  --seed 1 --timeout 60 --command /absolute/path/to/racket -l herbie
```

`--command` must be the final option; its remaining arguments are passed as an
argument vector without a shell. The external process has a wall-clock deadline
covering startup and search, and its process group is killed and reaped on
timeout or cancellation. Herbie also receives its per-expression timeout.

Each prepared directory permits one execution attempt. Failed attempts retain
logs and outputs; retry into a freshly prepared directory. Herbie's `improve`
command can exit zero after an internal crash and print the original expression.
The adapter treats its crash/error/timeout markers as failures. It also rejects
changed or missing domains, while accepting equivalent chained or split bounds.

Artifacts include the original source, input and improved FPCore, the custom
platform snapshot, stdout/stderr logs and a manifest with source, adapter,
platform, command-file and proposal hashes, command arguments, seed, deadline
and execution outcome. `validated` remains false. No secrets are collected.

## Qualification for phase 2

Pass a proposal through the existing original-C FP64 semantic gate, same-source
FP32 control, low-precision accuracy tests, backend capability checks, executed
precision audit and target measurements. Keep the input contract, tolerances and
observable outputs fixed. Freeze the source before using untouched holdouts.
Use the [experiment driver guide](experiment-driver-guide.md) and
[plan template](experiment-plan-template.md) before a scored campaign.

A result can be a pure low-precision reformulation, a selective mixed-precision
repair, an unchanged expression, or a full wider fallback. Classify it from the
resulting computation and audit. An unchanged expression is not recovery, and
an output cast does not make a full FP32 computation a selective repair.

## Development evidence

Development on 2026-11-04 used pinned Herbie
`4df89bf82ff82e603b430ff26f7ce1a605bfa234`, Racket 8.7 and CPU Torch. With seed 1
and a 60-second process budget per expression:

| Synthetic example | Development inputs | Original maximum relative error | Proposal maximum relative error |
| --- | --- | --- | --- |
| FP32 `sqrt(x+1)-sqrt(x)` | 4,097 logarithmically spaced values in `[1, 1e8]` | 4.65 | 1.14e-7 |
| FP16 `(x*x-y*y)/(x-y)` | 101 × 101 grid, `x` in `[100,120]`, `y` in `[90,99]` | 0.0232 | 0.000329 |

Errors use FP64 evaluation of a stable equivalent expression on the actual
quantized inputs. The FP16 result is `x+y`: a pure FP16 reformulation, with
bit-identical original FP32/FP64 controls. The FP32 example retains the FP64 path.
These are adapter smoke tests, with no original C oracle, accelerator validation,
performance or independent holdout claim. Raw plans, attempts and metrics are
local artifacts under `runs/herbie-adapter-20261104/`; failed development attempts
are retained, including an early adapter version that misclassified Herbie's
crash fallback as a proposal. The current regression tests reject that behavior.

[Tests](../tests/test_herbie.py) exercise refusal paths, deterministic preparation,
cast placement, broadcasting, dtype controls, domain preservation, failed jobs,
tampering and timeout cleanup. The optional native test checks all finite FP16
values and adjacent positive midpoints against Torch conversion, signed zeros,
overflow and random values, then runs a real FP16 Herbie round trip:

```sh
LASSI_HERBIE_RACKET=/absolute/path/to/racket \
PLTUSERHOME=/absolute/path/to/herbie-racket-user \
uv run --locked --extra dev --extra globus --extra roofline \
  python -m pytest tests/test_herbie.py -q
```

No broad phase 2 coverage is claimed: reductions, recurrences and stateful Torch
modules still need additional deterministic lowering or a separately scoped
hybrid approach.

The [five archived Torch-model trial](experiments/herbie-five-torch-20261104/RESULTS.md)
tested unchanged ATAX, GESUMMV, covariance, correlation and Deriche candidates.
All five were rejected by the current extraction contract before native Herbie
execution; the report records each exact limitation and every attempted case.

### Arithmetic regions inside larger models

`lassi_x.herbie_regions.discover(source, class_name, precision)` statically finds
maximal arithmetic expressions over names and constants inside `forward`.
Matrix operations, reductions, indexing, helper calls, and control flow can
surround these regions. Discovery does not execute the model or infer tensor
metadata. It accepts `nn.Module` spelling and surrounding helper methods.

Each returned `Region` contains a source hash, location, standalone wrapper
`source`, and `program()`. Save the wrapper and use the existing `prepare` and
`optimize` workflow with class name `Region`, explicit boundary domains, and the
appropriate precision platform. Pass the successful Herbie FPCore output to
`reinsert(original_source, region, improved_fpcore)` to obtain a model proposal.
Reinsertion checks the original hash and region identity. Apply one region at a
time, then rediscover against the changed source for another proposal.

The generated local helper checks all boundary values' tensor dtype and device;
otherwise it evaluates the original expression. Unsupported operations stay in
place. Domains must describe intermediate region inputs, not merely model inputs.
The existing external numerical gates remain required. Discovery is syntactic
coverage, not successful optimization, a precision audit, or numerical acceptance.
Calls within expressions are boundaries, so eligible arithmetic children can be
found without extracting a whole expression. Nested function scopes are excluded.
No automatic integration into the compensation worker is added.

Development-only static inspection of the unchanged five snapshots in
`runs/herbie-five-torch-20261104/inputs/`, using their recorded class names and
binary16, found 0 regions in ATAX, 1 in GESUMMV, 1 in covariance, 1 in correlation,
and 15 in Deriche. Thus four models expose at least one syntactically supported
region. This was a frontend development check, not a new numerical campaign:
no Herbie searches or model forward executions were performed on those snapshots.
The original five-model campaign outcomes remain unchanged. In particular,
covariance's small denominator expression does not imply its matrix accumulation
can be repaired, and Deriche's region count says nothing about recurrence accuracy.

### Opt-in Torch FX path

`lassi_x.herbie_fx` accepts a trusted `torch.fx.GraphModule`. The caller explicitly
captures the model with `torch.fx.symbolic_trace(model)`; tracing executes Python
with symbolic inputs and may execute side effects. It does not support arbitrary
data-dependent control flow. Helper methods are normally traced through when
traceable. No source module is imported automatically by the adapter.

`discover(graph, precision)` finds expression roots and follows supported producer
dependencies across assignments, including elementary Torch functions and explicit
positional `.to(torch.dtype)` calls. Matrix operations and other opaque calls
become boundary inputs; expansion does not cross an opaque operation because it
may mutate tensors. Supported roots can overlap: choose one, reinsert, and
rediscover. The boundary contract currently requires a uniform tensor dtype;
other dtype/scalar combinations run the original expression through the guard.
This does not yet infer mixed boundary types or automatically measure domains.

Use `region.program()` with the existing FPCore/Herbie workflow and
`herbie_fx.reinsert(graph, region, improved_fpcore)` for a copied graph proposal.
Opaque operations retain their graph position and execute once. Intermediate
arithmetic nodes can remain unused; they are deliberately not globally removed
because arbitrary graph operations may have side effects. Only internally
generated wrapper code is executed during reinsertion. Graph capture, extraction,
and rewriting use no language model. Herbie search needs a recorded seed and
bounded budget as before.

`herbie_fx.promote_matmul(graph, node_name)` supplies a separate deterministic
precision proposal for positional `torch.matmul` or `@` nodes: equal FP16/BF16
operands are converted to FP32 and the result is converted back. Other dtypes
retain the original operation. This is not a Herbie transformation or a certificate
of hardware accumulation behavior. Reduction promotion, compensated summation,
automatic region domain inference, and automatic repair selection remain future
work. Validate each proposal against the reference before accepting it.

Development tests cover cross-assignment cancellation repair with a supplied
stable expression, FP64 fallback, a single opaque matmul boundary, mutation
barriers, and matmul precision proposals. These are unit tests, not evidence of
Herbie search success or accuracy recovery on the five-model campaign.

### Opaque helper-method capture

`herbie_fx.capture_with_leaf_methods(model, ("_scan",))` captures a trusted model
while keeping the selected helpers as runtime module calls. It copies the model
and uses an isolated subclass; the original class is not patched. Surrounding
Python still executes during capture. This interface is for stateless numerical
helpers; helpers sharing mutable state with surrounding forward code are outside
its contract. Runtime calls retain dynamic shape behavior, so their branches and
loops need not be expanded into the FX graph. Region extraction treats those
calls as opaque barriers. No LLM or automatic helper selection is involved.

The explicit-FP64 Deriche development trial successfully captured with `_scan`
as a leaf and exposed 45 potentially overlapping binary64 expression roots.
Source and captured graph matched exactly on 4x4 and 16x17 inputs. See
[the trial report](experiments/herbie-deriche-leaf-20261104/RESULTS.md); no Herbie
search or numerical improvement is established by that capture test.

### Frozen Stage 2 execution

The [schema-1 deterministic Stage 2 step](stage2-deterministic.md) replays explicit
Herbie results and precision proposals, validates them in fixed order, and selects
only a passing strict improvement. Search and domain preparation are separate;
no model calls or adaptive search occur inside the step.
