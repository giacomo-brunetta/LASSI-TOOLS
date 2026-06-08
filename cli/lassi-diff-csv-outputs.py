#!/usr/bin/env python3
"""Report element-wise CSV mismatches; optionally dump to JSON."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--golden-csv", required=True, help="Path to the golden/oracle CSV file.")
    p.add_argument("--candidate-csv", required=True, help="Path to the candidate CSV file.")
    p.add_argument("--output-path", default=None, help="Optional path to save the mismatch report as JSON.")
    p.add_argument("--max-rows", type=int, default=20, help="Maximum number of mismatches to report.")
    a = p.parse_args()
    from lassi.verification.csv_tools import diff_csv_outputs_impl
    return run_async(
        diff_csv_outputs_impl(
            golden_csv=a.golden_csv,
            candidate_csv=a.candidate_csv,
            output_path=a.output_path,
            max_rows=a.max_rows,
        )
    , title="CSV element-wise diff")


if __name__ == "__main__":
    raise SystemExit(main())
