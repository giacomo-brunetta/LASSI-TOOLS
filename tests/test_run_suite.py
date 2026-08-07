from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments" / "paper"


def _load_run_suite():
    """Import run_suite.py, which lives outside the installed package."""
    sys.path.insert(0, str(EXPERIMENTS))
    try:
        spec = importlib.util.spec_from_file_location("run_suite", EXPERIMENTS / "run_suite.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(EXPERIMENTS))


run_suite = _load_run_suite()


@pytest.mark.parametrize(
    ("error", "timed_out", "expected"),
    [
        # The failure that cost fifteen consecutive runs: every cell must reduce
        # to one signature so the breaker recognizes them as the same fault.
        ("RuntimeError: Connection error.", False, "RuntimeError"),
        ("RuntimeError: Error code: 400 - {'error': ...}", False, "RuntimeError"),
        (
            "RemoteCallTimeoutError: put_file on a100-node got no response",
            False,
            "RemoteCallTimeoutError",
        ),
        ("", True, "timeout"),
        ("", False, ""),
    ],
)
def test_signature_reduces_failures_to_a_comparable_value(
    error: str, timed_out: bool, expected: str
) -> None:
    assert run_suite._signature(error, timed_out) == expected


def test_signature_ignores_error_text_that_varies_per_kernel() -> None:
    first = run_suite._signature("RuntimeError: Connection error. (gemm)", False)
    second = run_suite._signature("RuntimeError: Connection error. (3mm)", False)
    assert first == second


def test_error_is_read_from_the_envelope() -> None:
    assert run_suite._error({"error": "RuntimeError: Connection error."}) == (
        "RuntimeError: Connection error."
    )
    assert run_suite._error({"ok": False}) == ""
    assert run_suite._error(None) == ""


def _breaker(signatures: list[str], limit: int) -> int:
    """Replay the runner's consecutive-failure accounting.

    Args:
        signatures: One signature per failed cell, in matrix order.
        limit: Value of --max-consecutive-failures.

    Returns:
        Number of cells processed before the breaker tripped.
    """
    consecutive = 0
    last = ""
    for index, signature in enumerate(signatures, start=1):
        consecutive = consecutive + 1 if signature == last else 1
        last = signature
        if limit and consecutive >= limit:
            return index
    return len(signatures)


def test_breaker_trips_on_three_identical_failures() -> None:
    assert _breaker(["RuntimeError"] * 20, 3) == 3


def test_breaker_tolerates_unrelated_failures() -> None:
    mixed = ["RuntimeError", "ValueError", "RuntimeError", "ValueError"]
    assert _breaker(mixed, 3) == len(mixed)


def test_breaker_disabled_runs_the_whole_matrix() -> None:
    assert _breaker(["RuntimeError"] * 20, 0) == 20


def test_parser_rejects_a_negative_breaker_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_suite.py", "--max-consecutive-failures", "-1"])
    with pytest.raises(SystemExit):
        run_suite._arguments()


def test_breaker_defaults_to_three(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_suite.py"])
    assert run_suite._arguments().max_consecutive_failures == 3
