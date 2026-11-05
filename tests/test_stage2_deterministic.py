import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import torch
from torch import fx

from lassi_x.herbie_fx import discover
from lassi_x.stage2_deterministic import Plan, Proposal, Validation, run


class Model(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sqrt(x + 1) - torch.sqrt(x)


def test_frozen_replay(tmp_path: Path) -> None:
    graph = fx.symbolic_trace(Model())
    region = discover(graph)[-1]
    core = (
        "(FPCore (arg0) :precision binary32 :pre (and (<= 1 arg0 100000000)) "
        "(/ 1 (+ (sqrt (+ arg0 1)) (sqrt arg0))))"
    )
    proposal = Proposal("stable", "herbie", region.root, core, (("v0", 1, 100000000),))

    def sha(b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    plan = Plan(
        sha(b"source"), sha(graph.code.encode()), sha(b"{}"), sha(b"{}"), "binary32", (proposal,)
    )
    calls = []

    def validate(candidate: fx.GraphModule, precision: str, identity: str) -> Validation:
        calls.append(identity)
        x = torch.tensor([1e8], dtype=torch.float32)
        error = abs(candidate(x).item() - 0.00005)
        return Validation(True, True, error < 1e-8, True, error, "a" * 64)

    for name in ("first", "second"):
        selected = run(
            graph,
            plan,
            source="source",
            contract=b"{}",
            environment=b"{}",
            output=tmp_path / name,
            validate=validate,
        )
        assert selected is not None
    assert (tmp_path / "first/result.json").read_bytes() == (
        tmp_path / "second/result.json"
    ).read_bytes()
    assert calls == ["baseline", "stable", "baseline", "stable"]
    with pytest.raises(ValueError, match="identity"):
        run(
            graph,
            plan,
            source="changed",
            contract=b"{}",
            environment=b"{}",
            output=tmp_path / "bad",
            validate=validate,
        )
    assert not (tmp_path / "bad").exists()
    report = json.loads((tmp_path / "first/result.json").read_text())
    assert report["selected"] == "stable"


def test_validation_rejects_nonfinite() -> None:
    with pytest.raises(ValueError):
        Validation(True, True, True, True, float("nan"), "a" * 64)


def test_invalid_domain_cannot_be_accepted(tmp_path: Path) -> None:
    graph = fx.symbolic_trace(Model())
    region = discover(graph)[-1]

    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    proposal = Proposal(
        "bad", "herbie", region.root, "(FPCore (arg0) :precision binary32 arg0)", (("v0", 1, 2),)
    )
    plan = Plan(
        sha(b"s"), sha(graph.code.encode()), sha(b"{}"), sha(b"{}"), "binary32", (proposal,)
    )
    calls: list[str] = []

    def validator(g: fx.GraphModule, p: str, identity: str) -> Validation:
        calls.append(identity)
        return Validation(True, True, False, True, 1, "b" * 64)

    assert (
        run(
            graph,
            plan,
            source="s",
            contract=b"{}",
            environment=b"{}",
            output=tmp_path / "domain",
            validate=validator,
        )
        is None
    )
    assert calls == ["baseline"]
    record = json.loads((tmp_path / "domain/result.json").read_text())
    assert record["records"][-1]["status"] == "incomplete"

    def blocked(g: fx.GraphModule, p: str, identity: str) -> Validation:
        return Validation(False, True, False, True, 1, "b" * 64)

    assert (
        run(
            graph,
            replace(plan, proposals=()),
            source="s",
            contract=b"{}",
            environment=b"{}",
            output=tmp_path / "blocked",
            validate=blocked,
        )
        is None
    )
    assert json.loads((tmp_path / "blocked/result.json").read_text())["status"] == "blocked"
