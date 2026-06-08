#!/usr/bin/env python3
"""Locate runtime hotspots with `perf record/report/script`; compare hotspot shifts."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_json_arg(p, "cases", "Hotspot cases (case_id, command(s), working_dir, env, metadata).", required=True)
    p.add_argument("--mode", default="differential", choices=["single", "differential"])
    p.add_argument("--no-callgraph", action="store_true",
                   help="Disable callgraph collection (perf record -g).")
    p.add_argument("--frequency", type=int, default=999)
    p.add_argument("--timeout-s", type=int, default=600)
    p.add_argument("--generate-flamegraph", action="store_true",
                   help="Generate FlameGraph SVG (stackcollapse-perf.pl + flamegraph.pl required).")
    p.add_argument("--artifact-dir", default=None)
    p.add_argument("--shell", default="bash")
    a = p.parse_args()
    from lassi.profiling.performance_tools import profile_hotspots_impl
    return run_async(profile_hotspots_impl(
        cases=get_json_arg(a, "cases"),
        mode=a.mode,
        callgraph=not a.no_callgraph,
        frequency=a.frequency,
        timeout_s=a.timeout_s,
        generate_flamegraph=a.generate_flamegraph,
        artifact_dir=a.artifact_dir,
        shell=a.shell,
    ), title="Hotspot profile")


if __name__ == "__main__":
    raise SystemExit(main())
