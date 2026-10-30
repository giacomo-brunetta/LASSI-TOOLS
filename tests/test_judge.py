from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from lassi_x.config import JudgeConfig, ModelConfig
from lassi_x.hermes import HermesTurn
from lassi_x.types import Diagnostic, Usage
from lassi_x.validation import OracleResult, ValidationResult, validate_candidate

from .test_validation import _setup

if TYPE_CHECKING:
    from pathlib import Path


def setup_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    response: str,
    *,
    completed: bool = True,
    tests_pass: bool = True,
) -> Any:
    config, backend = _setup(tmp_path)
    config.judge = JudgeConfig(model=ModelConfig(model="independent-reviewer"))
    calls = []

    class Session:
        def __init__(self, model: Any, **kwargs: Any) -> None:
            assert kwargs["toolsets"] == []
            assert "memory" not in kwargs
            assert kwargs["cwd"] != tmp_path / "workspaces/good"
            calls.append(kwargs)

        async def close(self) -> None:
            pass

        async def send(self, prompt: Any) -> Any:
            calls.append(json.loads(prompt))
            return HermesTurn(response, Usage(input_tokens=12), completed=completed)

    async def numerical(*args: Any, **kwargs: Any) -> Any:
        return ValidationResult(
            tests_pass,
            None if tests_pass else Diagnostic("equivalence", "wrong values"),
            np.array([1.0]),
        )

    monkeypatch.setattr("lassi_x.judge.HermesSession", Session)
    monkeypatch.setattr("lassi_x.validation._validate_correctness", numerical)
    return config, backend, calls


def run_review(config: Any, backend: Any, tmp_path: Path, attempt: str = "report") -> Any:
    return asyncio.run(
        validate_candidate(
            config,
            backend,
            "good",
            OracleResult(tmp_path / "oracle.npy", np.array([1.0])),
            tmp_path / attempt,
        )
    )


@pytest.mark.parametrize("verdict,accepted", [("approve", True), ("reject", False)])
def test_judge_accepts_or_rejects_and_reviews_every_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verdict: str, accepted: bool
) -> None:
    response = json.dumps(
        {
            "verdict": verdict,
            "summary": "review evidence",
            "findings": [] if accepted else ["candidate.py: forward returns cached output"],
        }
    )
    config, backend, calls = setup_review(tmp_path, monkeypatch, response)
    for attempt in ("first", "second"):
        result = run_review(config, backend, tmp_path, attempt)
        assert result.ok is accepted
        if not accepted:
            assert result.diagnostic.gate == "llm_judge"
            assert "cached output" in result.diagnostic.message
        directory = tmp_path / attempt / "judge"
        report = json.loads((directory / "report.json").read_text())
        assert report["status"] == ("passed" if accepted else "failed")
        assert report["usage"]["input_tokens"] == 12
        assert report["candidate_sha256"]
        evidence = json.loads((directory / "evidence.json").read_text())
        assert "def forward" in evidence["candidate"]["source"]
        assert "#include" in evidence["reference_sources"][0]["source"]
    assert len(calls) == 4


@pytest.mark.parametrize(
    "response,completed",
    [
        ("not json", True),
        ('{"verdict":"approve","summary":"ok","findings":[]}', False),
        ('{"verdict":"reject","summary":"bad","findings":[]}', True),
        ('{"verdict":"inconclusive","summary":"missing header","findings":[]}', True),
    ],
)
def test_uncertain_or_invalid_review_never_accepts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response: str, completed: bool
) -> None:
    config, backend, _ = setup_review(tmp_path, monkeypatch, response, completed=completed)
    with pytest.raises(RuntimeError, match="inconclusive"):
        run_review(config, backend, tmp_path)
    report = json.loads((tmp_path / "report/judge/report.json").read_text())
    assert report["status"] == "inconclusive"


def test_failed_tests_skip_judge_and_preserve_feedback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, calls = setup_review(tmp_path, monkeypatch, "", tests_pass=False)
    result = run_review(config, backend, tmp_path)
    assert not result.ok
    assert result.diagnostic.gate == "equivalence"
    assert calls == []
    assert json.loads((tmp_path / "report/judge/report.json").read_text())["status"] == "not_run"


def test_context_overflow_does_not_review_truncated_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, calls = setup_review(tmp_path, monkeypatch, "")
    config.judge.max_source_chars = 1000
    (tmp_path / "tiny.c").write_text("x" * 1001)
    with pytest.raises(RuntimeError, match="inconclusive"):
        run_review(config, backend, tmp_path)
    assert calls == []


def test_disabled_judge_does_not_call_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, backend, calls = setup_review(tmp_path, monkeypatch, "")
    config.judge = None
    assert run_review(config, backend, tmp_path).ok
    assert calls == []


def test_judge_timeout_blocks_acceptance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, backend, _ = setup_review(tmp_path, monkeypatch, "")
    config.judge.timeout_s = 0.01

    async def stalled(*args: Any, **kwargs: Any) -> Any:
        await asyncio.sleep(10)

    monkeypatch.setattr("lassi_x.judge.fetch_bytes", stalled)
    with pytest.raises(RuntimeError, match="inconclusive"):
        run_review(config, backend, tmp_path)
    report = json.loads((tmp_path / "report/judge/report.json").read_text())
    assert report["status"] == "inconclusive"
    assert "TimeoutError" in report["reason"]
