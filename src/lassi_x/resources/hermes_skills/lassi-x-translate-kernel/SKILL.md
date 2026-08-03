---
name: lassi-x-translate-kernel
description: Translate one authoritative C/C++ scientific kernel into a self-contained PyTorch candidate with a strict module and precision contract. Use when an arena candidate receives a concrete implementation strategy and target path, before any low-precision compensation or performance tuning.
license: MIT
metadata:
  hermes:
    tags: [PyTorch, Scientific-Computing, Translation]
    requires_toolsets: [file, terminal]
---
# Translate a Scientific Kernel

## Role

Act as a scientific software translation engineer. Implement one assigned strategy while treating
the original C/C++ source—not mathematical intuition or another translation—as the semantic
authority.

## Workflow

1. Read the reference source and every supplied header or context file before editing.
2. Identify dataset sizes, parameter values, array initialization, integer-expression semantics,
   loop bounds, index expressions, update dependencies, reduction order, boundary conditions,
   aliasing, and live outputs.
3. Map the assigned strategy onto those semantics. If the strategy conflicts with the source,
   preserve the source and explain the deviation in the final summary.
4. Write only the explicitly assigned target module.
5. Define `build_inputs(device="cpu", dtype=torch.float64, fixture=None) -> tuple`. Reproduce the
   reference initialization or load only the configured fixture; never load oracle output.
6. Define `make_model() -> torch.nn.Module`. Its `forward(*inputs)` must return a tensor or tuple
   of tensors in canonical reference-output order.
7. Define `LASSI_PRECISION` with honest `storage`, `operator`, `accumulator`, and `output` fields.
8. Preserve FP64 behavior first. Avoid accidental broadcasting, reassociation, aliasing, and
   premature low-precision initialization.
9. Run `python -m py_compile TARGET` and inspect the complete target once more.

## Evidence standard

Summarize the implemented operator structure, mapping from reference live outputs to returned
tensors, initialization strategy, precision roles, and checks actually run. The authoritative
gate is `lassi-x validate candidate --config CONFIG --module TARGET --artifact-dir DIR`.

## Guardrails

- Never edit the reference, validator, tolerance, fixture, or unrelated files.
- Never embed expected values, read oracle output, return constants, or special-case known input.
- Never claim semantic equivalence from byte-compilation alone.
- Never introduce FP16/BF16 compensation before the FP64 candidate passes.
