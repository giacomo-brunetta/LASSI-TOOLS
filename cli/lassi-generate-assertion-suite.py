#!/usr/bin/env python3
"""Generate a shared assertion suite + harness metadata for both implementations."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-a", required=True)
    p.add_argument("--source-b", required=True)
    p.add_argument("--task-type", required=True,
                   choices=["C_TO_C_OPTIMIZATION", "C_TO_TORCH_TRANSLATION"])
    add_json_arg(p, "entrypoints", "Entrypoints to assert against (JSON list).")
    add_json_arg(p, "existing-tests", "Existing test file paths (JSON list).")
    add_json_arg(p, "semantic-hints", "Semantic hints for generated assertions (JSON list).")
    add_json_arg(p, "numeric-tolerance", "Tolerance, e.g. {\"rtol\":1e-5,\"atol\":1e-6}.")
    p.add_argument("--timeout-s", type=int, default=120)
    a = p.parse_args()
    from lassi.verification.verification_tools import generate_assertion_suite_impl
    return run_async(generate_assertion_suite_impl(
        source_a=a.source_a,
        source_b=a.source_b,
        task_type=a.task_type,
        entrypoints=get_json_arg(a, "entrypoints"),
        existing_tests=get_json_arg(a, "existing-tests"),
        semantic_hints=get_json_arg(a, "semantic-hints"),
        numeric_tolerance=get_json_arg(a, "numeric-tolerance"),
        timeout_s=a.timeout_s,
    ), title="Assertion suite generation")


if __name__ == "__main__":
    raise SystemExit(main())
