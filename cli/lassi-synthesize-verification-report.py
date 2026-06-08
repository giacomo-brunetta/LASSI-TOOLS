#!/usr/bin/env python3
"""Aggregate verification tool results into JSON + markdown report."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task-id", default=None, help="Optional verification task id.")
    p.add_argument("--task-type", default="C_TO_C_OPTIMIZATION",
                   choices=["C_TO_C_OPTIMIZATION", "C_TO_TORCH_TRANSLATION"])
    add_json_arg(p, "tool-results",
                 "Verification tool JSON objects to aggregate (list or single dict).")
    p.add_argument("--output-dir", default=".verify/reports")
    a = p.parse_args()
    from lassi.verification.verification_tools import synthesize_verification_report_impl
    return run_async(synthesize_verification_report_impl(
        task_id=a.task_id,
        task_type=a.task_type,
        tool_results=get_json_arg(a, "tool-results"),
        output_dir=a.output_dir,
    ), title="Verification report")


if __name__ == "__main__":
    raise SystemExit(main())
