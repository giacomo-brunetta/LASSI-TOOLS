"""Generation-accuracy metrics for arena runs."""

from __future__ import annotations

import math
from typing import Any

from .types import Candidate, Status


def pass_at_k(n: int, correct: int, k: int) -> float:
    """Estimate the probability that at least one of ``k`` samples passes.

    Args:
        n: Total generated samples.
        correct: Samples that passed the external validator.
        k: Number of samples made available to the estimator.

    Returns:
        The standard unbiased pass@k estimator.

    Raises:
        ValueError: If the counts do not satisfy ``0 <= correct <= n`` and
            ``1 <= k <= n``.
    """
    if n < 1 or not 0 <= correct <= n or not 1 <= k <= n:
        raise ValueError("pass@k requires n >= 1, 0 <= correct <= n, and 1 <= k <= n")
    if n - correct < k:
        return 1.0
    return 1.0 - math.comb(n - correct, k) / math.comb(n, k)


def candidate_accuracy(candidates: list[Candidate]) -> dict[str, Any]:
    """Summarize pre-repair and post-repair candidate correctness.

    The arena deliberately assigns materially different planner strategies, so
    its candidates are not IID samples from one identical prompt. The returned
    pass@k values are therefore labelled as arena estimates; paper-level standard
    pass@k requires repeated IID generations in addition to these diagnostics.

    Args:
        candidates: All candidates produced for one kernel run.

    Returns:
        Counts, rates, repair recovery, and pass@k estimates.
    """
    n = len(candidates)
    initial = sum(
        candidate.status == Status.OK and candidate.correction_rounds == 0
        for candidate in candidates
    )
    final = sum(candidate.status == Status.OK for candidate in candidates)
    recovered = sum(
        candidate.status == Status.OK and candidate.correction_rounds > 0
        for candidate in candidates
    )
    return {
        "samples": n,
        "initial_passes": initial,
        "final_passes": final,
        "recovered_by_repair": recovered,
        "initial_pass_rate": initial / n if n else 0.0,
        "final_pass_rate": final / n if n else 0.0,
        "kernel_solved": final > 0,
        "arena_pass_at_k": {
            "initial": {str(k): pass_at_k(n, initial, k) for k in range(1, n + 1)},
            "final": {str(k): pass_at_k(n, final, k) for k in range(1, n + 1)},
        },
        "sampling_note": (
            "Arena candidates use distinct planner-assigned strategies and are not IID; "
            "treat these as arena success estimates, not canonical benchmark pass@k."
        ),
    }
