from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

import lassi_x.arena as arena
from lassi_x.config import RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.hermes import HermesTurn
from lassi_x.types import Candidate, Status, Usage
from lassi_x.validation import build_oracle

from .test_config import minimal_config
from .test_validation import BAD_MODULE, C_REFERENCE, GOOD_MODULE

if TYPE_CHECKING:
    import pytest


def test_parse_json_extracts_array_from_model_commentary() -> None:
    text = (
        'I considered ["initial"] approaches.\n'
        '[{"name":"one","plan":"do it"},{"name":"two","plan":"do more"}]\nDone.'
    )
    assert arena._parse_json(text) == [
        {"name": "one", "plan": "do it"},
        {"name": "two", "plan": "do more"},
    ]


def test_system_prompts_define_concrete_roles_without_project_branding() -> None:
    assert "scientific-computing architect" in arena.PLANNER_SYSTEM
    assert "do not create, edit, or delete files" in arena.PLANNER_SYSTEM
    assert "scientific software engineer" in arena.CANDIDATE_SYSTEM
    assert "original C/C++ source is the semantic authority" in arena.CANDIDATE_SYSTEM
    assert "LASSI-X" not in arena.PLANNER_SYSTEM
    assert "LASSI-X" not in arena.CANDIDATE_SYSTEM


class FakeHermesSession:
    def __init__(
        self,
        model: object,
        *,
        cwd: Path,
        system_prompt: str,
        toolsets: list[str],
        role: str,
    ) -> None:
        del model, system_prompt, toolsets
        self.cwd = Path(cwd)
        self.role = role
        self.turn = 0

    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> FakeHermesSession:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def send(self, prompt: str) -> HermesTurn:
        self.turn += 1
        if self.role == "planner":
            text = json.dumps(
                [
                    {"name": "direct", "plan": "direct operations"},
                    {"name": "vector", "plan": "vector operations"},
                    {"name": "einsum", "plan": "einsum operations"},
                ]
            )
            return HermesTurn(text, Usage())
        target = self.cwd / "candidate.py"
        if self.turn == 1:
            if self.role == "c1":
                target.write_text(GOOD_MODULE)
            elif self.role == "c2":
                target.write_text("def broken(:\n")
            else:
                target.write_text(BAD_MODULE)
        else:
            assert "Correction round" in prompt
            target.write_text(GOOD_MODULE)
        return HermesTurn("done", Usage(input_tokens=1, output_tokens=1))


def test_arena_generates_three_and_repairs_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    config = RunConfig.load(config_path)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    monkeypatch.setattr(arena, "HermesSession", FakeHermesSession)

    async def run() -> list[Candidate]:
        oracle = await build_oracle(config, run_dir)
        async with await ExecutionContext.start(
            config, run_dir, hermes_home=tmp_path / "hermes"
        ) as execution:
            candidates, _ = await arena.run_arena(config, oracle, run_dir, execution)
        return candidates

    candidates = asyncio.run(run())
    assert len(candidates) == 3
    assert all(candidate.status == Status.OK for candidate in candidates)
    assert [candidate.correction_rounds for candidate in candidates] == [0, 1, 1]
    assert all(
        candidate.module_path == run_dir / "workspaces" / candidate.candidate_id / "candidate.py"
        for candidate in candidates
    )
    staged = run_dir / "workspaces" / "c1" / "reference" / "tiny.c"
    assert staged.read_text() == C_REFERENCE
