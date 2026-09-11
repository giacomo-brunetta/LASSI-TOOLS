from __future__ import annotations

import asyncio
import json
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
import yaml

import lassi_x.arena as arena
from lassi_x.config import RunConfig
from lassi_x.execution import ExecutionContext, ResourceUnavailableError
from lassi_x.hermes import HermesTurn
from lassi_x.types import Candidate, Status, Usage
from lassi_x.validation import build_oracle

from .test_config import minimal_config
from .test_validation import BAD_MODULE, C_REFERENCE, GOOD_MODULE


def test_parse_json_extracts_array_from_model_commentary() -> None:
    text = (
        'I considered ["initial"] approaches.\n'
        '[{"name":"one","plan":"do it"},{"name":"two","plan":"do more"}]\nDone.'
    )
    assert arena._parse_json(text) == [
        {"name": "one", "plan": "do it"},
        {"name": "two", "plan": "do more"},
    ]


def test_strategy_parser_rejects_two_plausible_arrays() -> None:
    text = '[{"name":"example","plan":"example plan"}]\n[{"name":"real","plan":"real plan"}]'
    with pytest.raises(ValueError, match="unambiguous"):
        arena._parse_strategies(text, 1)


def test_system_prompts_define_concrete_roles_without_project_branding() -> None:
    assert "scientific-computing architect" in arena.PLANNER_SYSTEM
    assert "do not create, edit, or delete files" in arena.PLANNER_SYSTEM
    assert "scientific software engineer" in arena.CANDIDATE_SYSTEM
    assert "original C/C++ source is the semantic authority" in arena.CANDIDATE_SYSTEM
    assert "compatibility wiki" in arena.PLANNER_SYSTEM
    assert "lassi-x-compat-wiki" in arena.CANDIDATE_SYSTEM
    assert "lassi-x-accelerator-compatibility" in arena.PLANNER_SYSTEM
    assert "lassi-x-accelerator-compatibility" in arena.CANDIDATE_SYSTEM
    assert "LASSI-X" not in arena.PLANNER_SYSTEM
    assert "LASSI-X" not in arena.CANDIDATE_SYSTEM


def test_groq_generation_prompt_requires_compatibility_preflight(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"].append(
        {
            "type": "groq",
            "name": "groq",
            "queue_dir": str(tmp_path / "queue"),
            "precisions": ["fp16"],
        }
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)

    prompt = arena._generation_prompt(config, "c1", "vectorized", "workspace", ["tiny.c"])

    assert "Compiler compatibility preflight (required)" in prompt
    assert "groq-r01-groqflow" in prompt
    assert "lassi-x-compat-wiki targets" in prompt
    assert "lassi-x-compat-wiki op OPERATOR" in prompt
    assert "--target TARGET --precision PRECISION" in prompt
    assert "lassi-x-accelerator-compatibility" in prompt


def test_non_groq_generation_prompt_omits_compatibility_preflight(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    config = RunConfig.load(config_path)

    prompt = arena._generation_prompt(config, "c1", "vectorized", "workspace", ["tiny.c"])

    assert "Groq compatibility preflight (required)" not in prompt


class FakeHermesSession:
    def __init__(
        self,
        model: object,
        *,
        cwd: Path,
        system_prompt: str,
        toolsets: list[str],
        role: str,
        memory: object | None = None,
    ) -> None:
        del model, system_prompt, toolsets, memory
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


class RepairingPlannerSession(FakeHermesSession):
    async def send(self, prompt: str) -> HermesTurn:
        self.turn += 1
        if self.turn == 1:
            # Two different arrays of the same length: the planner has offered no
            # single answer, which is the shape the retry exists to repair.
            return HermesTurn(
                '[{"name":"a","plan":"one"}] and also [{"name":"b","plan":"two"}]',
                Usage(),
            )
        assert "Repair only the output shape" in prompt
        return HermesTurn(
            json.dumps(
                [
                    {"name": "direct", "plan": "direct operations"},
                    {"name": "vector", "plan": "vector operations"},
                ]
            ),
            Usage(),
        )


def test_planner_repairs_configurable_strategy_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = minimal_config(tmp_path)
    data["arena"] = {"candidates": 2, "planner_format_retries": 1}
    data["models"]["candidates"].pop()
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)
    monkeypatch.setattr(arena, "HermesSession", RepairingPlannerSession)
    strategies, record = asyncio.run(arena.plan_strategies(config, tmp_path))
    assert len(strategies) == 2
    assert len(record["attempts"]) == 2
    assert "parse_error" in record["attempts"][0]


class ShortPlannerSession(FakeHermesSession):
    async def send(self, prompt: str) -> HermesTurn:
        self.turn += 1
        return HermesTurn('[{"name":"only","plan":"one vectorized formulation"}]', Usage())


def test_planner_may_return_fewer_strategies_than_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A kernel with only one distinct vectorized formulation must not be padded."""
    data = minimal_config(tmp_path)
    data["arena"] = {"candidates": 2, "planner_format_retries": 1}
    data["models"]["candidates"].pop()
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)
    monkeypatch.setattr(arena, "HermesSession", ShortPlannerSession)
    strategies, record = asyncio.run(arena.plan_strategies(config, tmp_path))
    assert len(strategies) == 1
    assert len(record["attempts"]) == 1
    assert "parse_error" not in record["attempts"][0]


class GroqAwarePlannerSession(FakeHermesSession):
    async def send(self, prompt: str) -> HermesTurn:
        self.turn += 1
        assert "lassi-x-accelerator-compatibility" in prompt
        assert "groq-r01-groqflow" in prompt
        assert "coder to query" in prompt
        return HermesTurn('[{"name":"portable","plan":"use the shared compiled core"}]', Usage())


def test_groq_planner_receives_family_evidence_routing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = minimal_config(tmp_path)
    data["arena"] = {"candidates": 1}
    data["models"]["candidates"] = data["models"]["candidates"][:1]
    data["measure"]["backends"].append(
        {
            "type": "groq",
            "name": "groq",
            "queue_dir": str(tmp_path / "queue"),
            "precisions": ["fp16"],
        }
    )
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)
    monkeypatch.setattr(arena, "HermesSession", GroqAwarePlannerSession)

    strategies, _ = asyncio.run(arena.plan_strategies(config, tmp_path))

    assert strategies == ["portable\nuse the shared compiled core"]


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


def _health_context(
    tmp_path: Path,
    *,
    abandoned: dict[str, dict[str, str]],
    dead: dict[str, str],
) -> tuple[RunConfig, ExecutionContext]:
    """Build a config and a context stub carrying a chosen execution health."""
    data = minimal_config(tmp_path)
    data["execution"] = {
        "mode": "academy",
        "resources": {"harness": {}, "a100-node": {}, "groq-login": {}},
        "default_resource": "harness",
        "timeout_tolerant_resources": ["groq-login"],
    }
    config = RunConfig.model_validate(data)
    context = cast(
        "ExecutionContext",
        SimpleNamespace(
            dead_resources=dead,
            mcp=SimpleNamespace(abandoned_calls=abandoned),
            require_live_resources=ExecutionContext.require_live_resources,
        ),
    )
    # Bind the real method so the stub enforces the real rule.
    context.require_live_resources = partial(  # type: ignore[method-assign]
        ExecutionContext.require_live_resources, context
    )
    return config, context


def test_abandoned_call_on_an_intolerant_resource_discards_the_candidate(
    tmp_path: Path,
) -> None:
    config, context = _health_context(
        tmp_path,
        abandoned={"c1": {"a100-node": "get_file got no response within 300s"}},
        dead={},
    )
    discard = arena._execution_health(config, context, "c1")
    assert discard is not None
    assert "a100-node" in discard


def test_abandoned_groq_compile_does_not_discard_the_candidate(tmp_path: Path) -> None:
    """A cold GroqFlow compile is legitimately minutes long; give it the benefit."""
    config, context = _health_context(
        tmp_path,
        abandoned={"c1": {"groq-login": "execute got no response within 1500s"}},
        dead={},
    )
    assert arena._execution_health(config, context, "c1") is None


def test_another_candidates_abandoned_call_is_not_charged_to_this_one(
    tmp_path: Path,
) -> None:
    config, context = _health_context(
        tmp_path,
        abandoned={"c2": {"a100-node": "get_file got no response within 300s"}},
        dead={},
    )
    assert arena._execution_health(config, context, "c1") is None


def test_a_retired_resource_ends_the_run_rather_than_one_candidate(tmp_path: Path) -> None:
    config, context = _health_context(
        tmp_path,
        abandoned={},
        dead={"a100-node": "2 consecutive calls abandoned"},
    )
    with pytest.raises(ResourceUnavailableError) as caught:
        arena._execution_health(config, context, "c1")
    assert caught.value.resource == "a100-node"


def test_a_retired_tolerant_resource_still_ends_the_run(tmp_path: Path) -> None:
    """Tolerance excuses a slow call, not an agent that has stopped answering."""
    config, context = _health_context(
        tmp_path,
        abandoned={},
        dead={"groq-login": "2 consecutive calls abandoned"},
    )
    with pytest.raises(ResourceUnavailableError):
        arena._execution_health(config, context, "c1")
