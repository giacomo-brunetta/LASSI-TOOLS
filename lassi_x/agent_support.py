"""Shared mechanics for the pipeline's persistent agent sessions.

This module deliberately contains only workspace and bookkeeping helpers.  The
planner, candidate, compatibility, and compensation workflows retain their own
prompts, gates, and correction policies in their owning modules.
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
