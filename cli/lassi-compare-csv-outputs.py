#!/usr/bin/env python3
"""Compare two numeric CSV outputs (exact + tolerant) with error metrics."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--golden-csv", required=True, help="Path to the golden/oracle CSV file.")
    p.add_argument("--candidate-csv", required=True, help="Path to the candidate CSV file.")
    p.add_argument("--rtol", type=float, default=1e-6, help="Relative tolerance.")
    p.add_argument("--atol", type=float, default=1e-6, help="Absolute tolerance.")
    add_json_arg(p, "expected-shape", "Optional expected CSV array shape, e.g. [3,4]")
    a = p.parse_args()
    from lassi.verification.csv_tools import compare_csv_outputs_impl
    return run_async(
        compare_csv_outputs_impl(
            golden_csv=a.golden_csv,
            candidate_csv=a.candidate_csv,
            rtol=a.rtol,
            atol=a.atol,
            expected_shape=get_json_arg(a, "expected-shape"),
        )
    , title="CSV comparison")


if __name__ == "__main__":
    raise SystemExit(main())
