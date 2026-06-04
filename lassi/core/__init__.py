"""Core building blocks shared across LASSI tools.

Contains the compiler/executer abstractions, source-file representation,
data models, generic utilities, and the shared MCP helpers
(:mod:`lassi.core.mcp_helpers`) used by both ``performance_tools`` and
``verification_tools``. No MCP coupling lives here — these modules are
imported by every other subpackage.
"""
