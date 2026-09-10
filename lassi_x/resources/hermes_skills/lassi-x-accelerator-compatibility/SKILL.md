---
name: lassi-x-accelerator-compatibility
description: Plan, implement, or repair PyTorch operator structures for published Graphcore PopTorch, Cerebras CS-3, and GroqFlow compiler targets. Use when accelerator choice or ATen operator compatibility affects a translation strategy; use the exact wiki instead for function-level decisions.
license: MIT
metadata:
  hermes:
    tags: [Accelerator, Compiler, PyTorch, Planning, Compatibility]
    requires_toolsets: [skills]
---
# Design for Accelerator Compiler Compatibility

## Role

Act as a target-compatibility analyst. Use published canonical compile evidence to avoid known
operator dead ends while preserving the authoritative program semantics. Never turn a family
trend into a claim about one function or a complete model.

Read [references/platform-summary.md](references/platform-summary.md) when Graphcore PopTorch,
Cerebras CS-3, or GroqFlow is a target.

## Workflow

Choose the workflow matching the agent role.

### Planner

1. Identify every intended accelerator/compiler stack and precision. Do not substitute results
   from another vendor, compiler version, or the `torch-mlir-tosa` compiler target.
2. Use the family matrix and three-platform overlap in the reference to compare implementation
   structures. Prefer the shared compiled core for portable plans and use target strengths only
   when the plan is explicitly target-specific.
3. For each proposed strategy, name the expected nontrivial `aten.*` operator families, likely
   pressure points, and semantically faithful alternative structures.
4. Mark exact operators as coder preflight obligations. Without an exact wiki result supplied in
   context, do not state that an individual operator is compiled or rejected.

### Coder or repair agent

1. Run `lassi-x-compat-wiki targets` and select the exact published target. Current published
   target IDs are `graphcore-pod64-poptorch`, `alcf-cs3-cerebras-pytorch`,
   `groq-r01-groqflow`, and `torch-mlir-tosa`.
2. Inventory the actual `aten.*` operators produced or expected by the candidate. Do not treat a
   Torch-MLIR/TOSA result as evidence for accelerator execution.
3. Query every uncertain or nontrivial operator with:
   `lassi-x-compat-wiki op OPERATOR --target TARGET --precision PRECISION`.
   Add `--markdown` when the full canonical fixture, result, or compiler diagnostic is needed.
4. Search for nearby compiled operators with:
   `lassi-x-compat-wiki search PATTERN --target TARGET --precision PRECISION --supported`.
   An alternative is usable only if it preserves the reference semantics and passes FP64
   validation.
5. Treat `compiled`, `compile_rejected`, `needs_fixture`, and `not_applicable` as distinct states.
   Unknown and fixture-limited cases require evidence; they are not support.
6. Rerun full candidate validation and the real target compiler. Canonical operator evidence is a
   preflight signal, not proof that a complete graph will compile, fit, execute, or be correct.

## Evidence standard

Report the exact target ID, precision, queried operators, canonical statuses, wiki pages used,
semantic substitutions, and checks actually run. State whether each conclusion is family-level,
canonical operator-level, whole-graph compile evidence, or hardware execution evidence.

## Guardrails

- Never infer exact function support from a family percentage.
- Never call `needs_fixture`, `not_applicable`, missing evidence, or a different target “supported.”
- Never replace an operator with a merely similar one or weaken the reference semantics.
- Never equate canonical compilation with numerical correctness, performance, arbitrary-shape
  support, placement, or hardware execution.
- Never describe the Groq snapshot as native FP16 evidence or the CS-3 snapshot as wafer execution.
