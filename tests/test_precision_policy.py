from __future__ import annotations

from lassi_x.config import CompensationConfig
from lassi_x.precision_policy import MIXED_FORMAT_CONTRACT, TARGET_FORMAT_CONTRACT


def test_new_runs_default_to_target_format_only() -> None:
    assert CompensationConfig().arithmetic_policy == "target_format_only"
    assert CompensationConfig(arithmetic_policy="mixed").arithmetic_policy == "mixed"


def test_contract_separates_validation_and_target_execution() -> None:
    assert "FP32/FP64 branches remain available solely" in TARGET_FORMAT_CONTRACT
    assert "never regenerate the" in TARGET_FORMAT_CONTRACT
    assert "whole kernel are forbidden" in MIXED_FORMAT_CONTRACT
    assert "explicitly allowlisted" in MIXED_FORMAT_CONTRACT
