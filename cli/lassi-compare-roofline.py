#!/usr/bin/env python3
"""Compare reference and candidate roofline positions and utilization."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--roofline-result-path", required=True, help="Path to roofline_report.json.")
    add_json_arg(p, "policy", "Roofline comparison policy thresholds.")
    p.add_argument("--artifact-dir", default=None)
    a = p.parse_args()
    from lassi.profiling.performance_tools import compare_roofline_impl
    return run_async(compare_roofline_impl(
        roofline_result_path=a.roofline_result_path,
        policy=get_json_arg(a, "policy"),
        artifact_dir=a.artifact_dir,
    ), title="Roofline comparison")


if __name__ == "__main__":
    raise SystemExit(main())
