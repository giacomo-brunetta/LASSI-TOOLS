"""Record harness instructions without copying provider configuration or credentials."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from . import __version__
from .artifacts import atomic_write
from .skills import automation_skill_prompt, source_root


def assembled_system_prompt(system: str, role: str, toolsets: list[str], home: Path) -> str:
    """Match the role instructions supplied to Hermes by the worker."""
    return system + "\n\n" + automation_skill_prompt(role, home) if "skills" in toolsets else system


def save_instruction_snapshot(
    directory: Path, *, system: str, role: str, toolsets: list[str], home: Path
) -> Path:
    """Keep immutable per-initialization snapshots, including resumed sessions."""
    supplied = assembled_system_prompt(system, role, toolsets, home)
    root = source_root()
    record = {
        "schema_version": 1,
        "scope": "harness-supplied instructions; Hermes adds SDK guidance and optional memory",
        "lassi_x_version": __version__,
        "hermes_version": version("hermes-agent"),
        "role": role,
        "toolsets": toolsets,
        "system_prompt": supplied,
        "system_sha256": hashlib.sha256(supplied.encode()).hexdigest(),
        "skill_files": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        },
        "prompt_sources": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in (
                "candidate_generation.py",
                "compensation.py",
                "compatibility_repair.py",
                "judge.py",
                "precision_policy.py",
                "agent_support.py",
                "skills.py",
                "hermes_worker.py",
                "instruction_provenance.py",
            )
        },
    }
    payload = json.dumps(record, indent=2, sort_keys=True) + "\n"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    path = directory / "agent-instructions" / f"{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, payload)
    return path
