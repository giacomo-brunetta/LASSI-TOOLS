from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from lassi_x.accuracy import candidate_accuracy, pass_at_k
from lassi_x.types import Candidate, Status

if TYPE_CHECKING:
    from pathlib import Path


def test_pass_at_k_matches_standard_estimator() -> None:
    assert pass_at_k(3, 1, 1) == pytest.approx(1 / 3)
    assert pass_at_k(3, 1, 2) == pytest.approx(2 / 3)
    assert pass_at_k(3, 1, 3) == 1.0


def test_candidate_accuracy_separates_initial_and_repaired_passes(tmp_path: Path) -> None:
    candidates = [
        Candidate("c1", "model", "provider", "one", tmp_path / "c1", status=Status.OK),
        Candidate(
            "c2",
            "model",
            "provider",
            "two",
            tmp_path / "c2",
            status=Status.OK,
            correction_rounds=1,
        ),
        Candidate("c3", "model", "provider", "three", tmp_path / "c3", status=Status.REJECTED),
    ]
    metrics = candidate_accuracy(candidates)
    assert metrics["initial_passes"] == 1
    assert metrics["final_passes"] == 2
    assert metrics["recovered_by_repair"] == 1
    assert metrics["kernel_solved"] is True
    assert "not IID" in metrics["sampling_note"]
