from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from lassi_x.repair_history import RepairHistory, input_contract, parse_hypothesis

if TYPE_CHECKING:
    from pathlib import Path


SOURCE = """import torch
N = 4
def helper(dtype):
    return torch.ones(N, dtype=dtype)
def build_inputs(device='cpu', dtype=torch.float64):
    return (helper(dtype).to(device),)
class Model(torch.nn.Module):
    def forward(self, x):
        return x + x
"""


def test_frozen_builder_includes_helpers_but_not_forward() -> None:
    assert input_contract(SOURCE) == input_contract(SOURCE.replace("x + x", "x * 2"))
    assert input_contract(SOURCE) != input_contract(SOURCE.replace("N = 4", "N = 2"))
    assert input_contract(SOURCE) != input_contract(SOURCE.replace("torch.ones", "torch.zeros"))
    assert input_contract(SOURCE) == input_contract(
        "from lassi_x.precision import compensated_sum\n" + SOURCE
    )


def test_history_is_scoped_and_keeps_both_precision_attempts(tmp_path: Path) -> None:
    luna = RepairHistory(tmp_path, {"kernel": "dft", "model": "luna", "policy": "target"})
    terra = RepairHistory(tmp_path, {"kernel": "dft", "model": "terra", "policy": "target"})
    other = RepairHistory(tmp_path, {"kernel": "adi", "model": "luna", "policy": "target"})
    mixed = RepairHistory(tmp_path, {"kernel": "dft", "model": "luna", "policy": "mixed"})
    for precision in ("fp16", "bf16"):
        luna.record(SOURCE.encode(), {"precision": precision, "status": "rejected"})
    assert {e["precision"] for e in luna.entries()} == {"fp16", "bf16"}
    assert not terra.entries() and not other.entries() and not mixed.entries()
    assert all((luna.root / e["source_file"]).read_text() == SOURCE for e in luna.entries())


def test_strategy_revision_requires_reason_and_code_repeat_is_independent(tmp_path: Path) -> None:
    history = RepairHistory(tmp_path, {"kernel": "dft"})
    hypothesis = {"strategy_key": "sum:pairwise"}
    history.record(b"source", {"hypothesis": hypothesis, "semantic_fingerprint": "hash"})
    with pytest.raises(ValueError, match="revisit_reason"):
        history.reject_repetition(hypothesis)
    history.reject_repetition({**hypothesis, "revisit_reason": "correct tree padding at odd size"})
    assert history.repeated_source("hash")
    assert not history.repeated_source("new hash")


def test_hypothesis_cannot_be_just_a_technique_label() -> None:
    with pytest.raises(ValueError, match="required nonempty"):
        parse_hypothesis(json.dumps({"technique": "scaling"}), ["scaling"])
