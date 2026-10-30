"""Prevent historical schema imports from omitting evaluator layout metadata."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1] / "experiments/holdout-validation/prepare_fp16_holdout.py"
)
spec = importlib.util.spec_from_file_location("fp16_holdout_prepare", SCRIPT)
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_missing_historical_stride_is_rejected_before_staging():
    schema = [{"argument": "data", "kind": "tensor", "shape": [1400, 1200], "integer_dtype": None}]
    with pytest.raises(ValueError, match="tensor layout"):
        prepare.validate_schema(schema)
    schema[0]["stride"] = [1200, 1]
    prepare.validate_schema(schema)


def test_scalar_tensor_layout_has_zero_rank():
    prepare.validate_schema(
        [{"argument": "rr", "kind": "tensor", "shape": [], "stride": [], "integer_dtype": None}]
    )


def test_inconsistent_layout_rank_is_rejected():
    with pytest.raises(ValueError, match="tensor layout"):
        prepare.validate_schema(
            [
                {
                    "argument": "data",
                    "kind": "tensor",
                    "shape": [4, 4],
                    "stride": [1],
                    "integer_dtype": None,
                }
            ]
        )
