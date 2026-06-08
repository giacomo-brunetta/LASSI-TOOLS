#!/usr/bin/env python3
"""Collect CPU perf counters with `perf stat`; derive IPC/cache/branch metrics."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_json_arg(p, "cases",
                 "Perf stat cases with case_id, command/command_a/command_b, working_dir, environment, metadata.",
                 required=True)
    p.add_argument("--mode", default="differential", choices=["single", "differential"])
    add_json_arg(p, "events", "perf stat event names (JSON list of strings).")
    p.add_argument("--repeat", type=int, default=5)
    p.add_argument("--timeout-s", type=int, default=600)
    p.add_argument("--artifact-dir", default=None)
    p.add_argument("--no-json-output", action="store_true",
                   help="Disable perf JSON output even when supported.")
    p.add_argument("--shell", default="bash")
    a = p.parse_args()
    from lassi.profiling.performance_tools import collect_perf_stats_impl
    return run_async(collect_perf_stats_impl(
        cases=get_json_arg(a, "cases"),
        mode=a.mode,
        events=get_json_arg(a, "events"),
        repeat=a.repeat,
        timeout_s=a.timeout_s,
        artifact_dir=a.artifact_dir,
        use_json_output_if_available=not a.no_json_output,
        shell=a.shell,
    ), title="Perf-stat results")


if __name__ == "__main__":
    raise SystemExit(main())
