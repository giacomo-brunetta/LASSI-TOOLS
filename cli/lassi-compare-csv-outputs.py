#!/usr/bin/env python3
"""Compare two numeric CSV outputs.

Two modes:
  * ``summary`` (default) — shape/exact/allclose verdict + max abs/rel error +
    classification (IDENTICAL / ACCEPTABLE_NUMERIC_DRIFT / DIFF_EXISTS).
  * ``elementwise`` — list of per-cell mismatches (up to ``--max-rows``);
    optionally persisted to ``--output-path`` as JSON.
"""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--golden-csv", required=True, help="Path to the golden/oracle CSV file.")
    p.add_argument("--candidate-csv", required=True, help="Path to the candidate CSV file.")
    p.add_argument("--mode", choices=["summary", "elementwise"], default="summary",
                   help="summary = tolerant pass/fail verdict; elementwise = per-cell mismatch list.")
    p.add_argument("--rtol", type=float, default=1e-6, help="Relative tolerance (summary mode).")
    p.add_argument("--atol", type=float, default=1e-6, help="Absolute tolerance (summary mode).")
    add_json_arg(p, "expected-shape", "Optional expected CSV array shape, e.g. [3,4] (summary mode).")
    p.add_argument("--output-path", default=None,
                   help="Optional JSON output path (elementwise mode).")
    p.add_argument("--max-rows", type=int, default=20,
                   help="Max mismatches to report (elementwise mode).")
    a = p.parse_args()

    if a.mode == "summary":
        from lassi.verification.csv_tools import compare_csv_outputs_impl
        coro = compare_csv_outputs_impl(
            golden_csv=a.golden_csv,
            candidate_csv=a.candidate_csv,
            rtol=a.rtol,
            atol=a.atol,
            expected_shape=get_json_arg(a, "expected-shape"),
        )
        return run_async(coro, title="CSV comparison (summary)")

    from lassi.verification.csv_tools import diff_csv_outputs_impl
    coro = diff_csv_outputs_impl(
        golden_csv=a.golden_csv,
        candidate_csv=a.candidate_csv,
        output_path=a.output_path,
        max_rows=a.max_rows,
    )
    return run_async(coro, title="CSV comparison (elementwise)")


if __name__ == "__main__":
    raise SystemExit(main())
