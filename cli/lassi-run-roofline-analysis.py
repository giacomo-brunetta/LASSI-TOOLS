#!/usr/bin/env python3
"""Run roofline analysis from benchmark timing, workload, and hardware model artifacts."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark-result-path", required=True, help="Path to run_benchmark result.json.")
    p.add_argument("--workload-model-path", required=True, help="Path to workload model JSON.")
    p.add_argument("--hardware-model-path", required=True, help="Path to hardware_model JSON.")
    p.add_argument("--precision", default="fp32", help="Precision key, e.g. fp32.")
    p.add_argument("--memory-level", default="dram", help="Bandwidth level key, e.g. dram.")
    p.add_argument("--mode", default="differential", choices=["single", "differential"])
    p.add_argument("--artifact-dir", default=None)
    add_json_arg(p, "policy", "Optional differential roofline policy thresholds.")
    a = p.parse_args()
    from lassi.profiling.performance_tools import run_roofline_analysis_impl
    return run_async(run_roofline_analysis_impl(
        benchmark_result_path=a.benchmark_result_path,
        workload_model_path=a.workload_model_path,
        hardware_model_path=a.hardware_model_path,
        precision=a.precision,
        memory_level=a.memory_level,
        mode=a.mode,
        artifact_dir=a.artifact_dir,
        policy=get_json_arg(a, "policy"),
    ), title="Roofline analysis")


if __name__ == "__main__":
    raise SystemExit(main())
