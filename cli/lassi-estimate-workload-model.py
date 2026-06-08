#!/usr/bin/env python3
"""Estimate FLOPs, bytes moved, and arithmetic intensity for roofline analysis."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_json_arg(p, "benchmark-cases",
                 "Cases with case_id, operation, metadata, optional manual_flops/manual_bytes.",
                 required=True)
    p.add_argument("--source-a", default=None, help="Optional reference source path.")
    p.add_argument("--source-b", default=None, help="Optional candidate source path.")
    p.add_argument("--estimation-mode", default="formula",
                   choices=["manual", "formula", "static_analysis", "agent_assisted"])
    p.add_argument("--artifact-dir", default=None)
    a = p.parse_args()
    from lassi.profiling.performance_tools import estimate_workload_model_impl
    return run_async(estimate_workload_model_impl(
        benchmark_cases=get_json_arg(a, "benchmark-cases"),
        source_a=a.source_a,
        source_b=a.source_b,
        estimation_mode=a.estimation_mode,
        artifact_dir=a.artifact_dir,
    ), title="Workload model (FLOPs / bytes / AI)")


if __name__ == "__main__":
    raise SystemExit(main())
