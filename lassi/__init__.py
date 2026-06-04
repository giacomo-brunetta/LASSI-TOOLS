"""LASSI Python package.

Subpackages:

- :mod:`lassi.core` — compiler, executer, source-file, data models, and shared MCP helpers.
- :mod:`lassi.profiling` — profiler primitives, gprof wrapper, and performance MCP tool implementations.
- :mod:`lassi.verification` — sanitizer builds, assertion suites, equivalence and fuzz testing, CSV diff utilities.
- :mod:`lassi.analysis` — translation/source-level analysis helpers shared between agents.
- :mod:`lassi.integrations` — wrappers for external toolchains (PyTorch export, torch-mlir, toolchain introspection).
- :mod:`lassi.prompt_dicts` — JSON prompt templates consumed by LASSI agents.

All MCP tool registrations live in ``LASSI_mcp.py`` at the repository root; this
package contains the implementations they call into.
"""
