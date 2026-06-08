#!/usr/bin/env python3
"""Aggregate benchmark/perf-stat/hotspot evidence into a differential verdict."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark-result-path", default=None,
                   help="Path to run_benchmark result.json.")
    p.add_argument("--perf-stats-result-path", default=None,
                   help="Path to collect_perf_stats result.json.")
    p.add_argument("--profile-result-path", default=None,
                   help="Path to profile_hotspots result.json.")
    add_json_arg(p, "policy", "Comparison policy thresholds.")
    p.add_argument("--artifact-dir", default=None)
    a = p.parse_args()
    from lassi.profiling.performance_tools import compare_performance_impl
    return run_async(compare_performance_impl(
        benchmark_result_path=a.benchmark_result_path,
        perf_stats_result_path=a.perf_stats_result_path,
        profile_result_path=a.profile_result_path,
        policy=get_json_arg(a, "policy"),
        artifact_dir=a.artifact_dir,
    ), title="Performance comparison verdict")


if __name__ == "__main__":
    raise SystemExit(main())
