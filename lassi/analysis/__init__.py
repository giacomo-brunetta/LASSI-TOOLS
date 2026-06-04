"""Source-level analysis helpers used by translator and verifier agents.

Currently contains :mod:`lassi.analysis.translation_utils`, which provides
deterministic seeding, tensor construction from specs, variant loading,
toolchain summaries, and artifact-path helpers. It is plain Python (no MCP
coupling) and is intended for reuse from generated scripts.

Artifact-level checks and CSV utilities live next door in
:mod:`lassi.verification`.
"""
