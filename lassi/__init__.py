"""LASSI Python package.

Subpackages:

- :mod:`lassi.core` — compiler, executer, source-file representation, shared
  utilities, and data models used across the rest of the package.
- :mod:`lassi.profiling` — profiler primitives (timers, CPU/GPU/ARM power
  probes) backing the ``lassi-execute-with-*`` and benchmark CLIs.
- :mod:`lassi.verification` — sanitizer build helpers, assertion suite
  scaffolding, equivalence/fuzz harness templates, and CSV diff utilities.
- :mod:`lassi.analysis` — translation/source-level analysis helpers shared
  between agents.
- :mod:`lassi.integrations` — wrappers for external toolchains (PyTorch
  export, torch-mlir lowering, toolchain introspection, hardware info, SODA).
- :mod:`lassi.utils` — small shared utilities (markdown rendering, etc.).

The runtime surface is the ``cli/lassi-*`` scripts (driven by the Claude Code
skills under ``.claude/skills/``) and the Pydantic-graph flow in
``graph/graph_flow.py``; this package contains the implementations those entry
points call into.
"""
