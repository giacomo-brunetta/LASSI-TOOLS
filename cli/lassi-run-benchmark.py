#!/usr/bin/env python3
"""Run stable timing benchmarks with hyperfine; emit common perf JSON schema."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_json_arg(p, "benchmark-cases",
                 "Benchmark cases with case_id, command/command_a/command_b, working_dir, environment, metadata.",
                 required=True)
    p.add_argument("--mode", default="differential", choices=["single", "differential"],
                   help="single or differential.")
    p.add_argument("--warmup", type=int, default=3)
    p.add_argument("--min-runs", type=int, default=10)
    p.add_argument("--max-runs", type=int, default=100)
    p.add_argument("--timeout-s", type=int, default=600)
    p.add_argument("--shell", default="bash")
    p.add_argument("--no-export-json", action="store_true", help="Disable raw hyperfine JSON export.")
    p.add_argument("--prepare-command", default=None)
    p.add_argument("--cleanup-command", default=None)
    p.add_argument("--artifact-dir", default=None)
    add_json_arg(p, "thresholds",
                 "Optional thresholds: min_effect_size_pct and max_cv_pct.")
    a = p.parse_args()
    from lassi.profiling.performance_tools import run_benchmark_impl
    return run_async(run_benchmark_impl(
        benchmark_cases=get_json_arg(a, "benchmark-cases"),
        mode=a.mode,
        warmup=a.warmup,
        min_runs=a.min_runs,
        max_runs=a.max_runs,
        timeout_s=a.timeout_s,
        shell=a.shell,
        export_json=not a.no_export_json,
        prepare_command=a.prepare_command,
        cleanup_command=a.cleanup_command,
        artifact_dir=a.artifact_dir,
        thresholds=get_json_arg(a, "thresholds"),
    ), title="Benchmark results")


if __name__ == "__main__":
    raise SystemExit(main())
