"""Shared mechanics for the pipeline's persistent agent sessions.

This module contains workspace and bookkeeping helpers plus policies shared by
every agent that can execute commands.  Role-specific prompts, gates, and
correction policies remain in their owning modules.
"""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING, Protocol

from .validation import fixture_relative_path

if TYPE_CHECKING:
    from pathlib import Path

    from .config import RunConfig
    from .execution import ExecutionContext
    from .hermes import HermesTurn
    from .types import Usage


BOUNDED_TOOL_OUTPUT_POLICY = """

Bounded tool output (hard requirement):
Policy version: `bounded-tool-output-v1`.
- Keep every tool response small and relevant. Before running a command, consider whether its
  output can grow with graph, tensor, file, directory, diff, trace, or log size.
- Never print complete compiler, Export, FX, TorchScript, or ONNX graphs; tensors or numerical
  artifacts; generated files; recursive directory listings; long logs or stack traces; or large
  diffs. Do not reread unchanged content already present in the conversation.
- Limit ordinary diagnostic output to at most 100 lines and approximately 8 KiB. Use targeted
  queries, filters, counts, summaries, and short head/tail excerpts.
- If complete output may be useful, redirect it to a workspace artifact and return only its path,
  byte or line count, command status, and a compact summary. Inspect further bounded excerpts only
  when they answer a specific unresolved question.
- Prefer shapes, dtypes, devices, finite-value counts, ranges, norms, aggregate error metrics,
  operator histograms, unsupported nodes, and a few selected examples over raw contents.
"""


class TurnRecorder(Protocol):
    """Structural type implemented by candidates and compensation variants."""

    usage: Usage
    turn_outcomes: list[dict[str, str | bool | int]]


def workspace_slug(value: str) -> str:
    """Return a tool-safe, bounded workspace identifier."""

    clean = re.sub(r"[^A-Za-z0-9._-]", "-", value)
    if len(clean) <= 64:
        return clean
    return f"{clean[:55]}-{hashlib.sha256(clean.encode()).hexdigest()[:8]}"


async def stage_reference_bundle(
    config: RunConfig,
    execution: ExecutionContext,
    workspace: str,
) -> list[str]:
    """Stage reference sources, context, and the optional fixture for an agent."""

    staged: list[str] = []
    for relative in [config.kernel.reference, *config.kernel.context]:
        source = config.resolve_project_path(relative)
        destination = f"reference/{source.name}"
        await execution.stage_bytes(workspace, destination, source.read_bytes())
        staged.append(destination)
    fixture = fixture_relative_path(config)
    if fixture is not None and config.oracle.input_fixture is not None:
        source = config.resolve_project_path(config.oracle.input_fixture)
        await execution.stage_bytes(workspace, fixture, source.read_bytes())
    return staged


def record_turn(owner: TurnRecorder, turn: HermesTurn) -> None:
    """Accumulate one agent turn's usage and normalized completion metadata."""

    owner.usage.add(turn.usage)
    owner.turn_outcomes.append(
        {
            "completed": turn.completed,
            "exit_reason": turn.exit_reason,
            "attempts": turn.attempts,
        }
    )


def attempt_diagnostic_dir(
    run_dir: Path,
    category: str,
    workspace: str,
    attempt: int,
) -> Path:
    """Create and return the artifact directory for one validation attempt."""

    path = run_dir / "diagnostics" / category / workspace / f"attempt-{attempt}"
    path.mkdir(parents=True, exist_ok=True)
    return path
