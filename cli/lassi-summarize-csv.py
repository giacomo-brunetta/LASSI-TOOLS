#!/usr/bin/env python3
"""Summarize a numeric CSV file: shape, size, range, mean/std, NaN/Inf."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--path", required=True, help="Path to the CSV file to summarize.")
    a = p.parse_args()
    from lassi.verification.csv_tools import summarize_csv_impl
    return run_async(summarize_csv_impl(a.path), title="CSV summary")


if __name__ == "__main__":
    raise SystemExit(main())
