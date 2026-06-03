from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HARNESS_PATH = os.environ.get("LASSI_HARNESS_PATH")
if HARNESS_PATH:
    sys.path.insert(0, str(Path(HARNESS_PATH).resolve().parent))
    import common_harness as harness
else:
    raise RuntimeError("LASSI_HARNESS_PATH is required")

ENTRYPOINT = 'main'
SIGNATURE = 'double(double)'
RTOL = 1e-12
ATOL = 1e-12
ASSERTION_CASES = [-2.0, -1.0, -0.0, 0.0, 1.0, 2.0, 16.0]


def _finite(value):
    arr = harness._to_numpy(value)
    return bool(np.isfinite(arr).all())


def main():
    impl_a = os.environ["IMPLEMENTATION_A_ARTIFACT"]
    impl_b = os.environ["IMPLEMENTATION_B_ARTIFACT"]
    harness.configure(impl_a, impl_b, ENTRYPOINT, SIGNATURE)
    failures = []
    assertions_run = 0
    for case in ASSERTION_CASES:
        a_out = harness.run_a(case)
        b_out = harness.run_b(case)
        assertions_run += 3
        if not _finite(a_out):
            failures.append({"input": case, "assertion": "implementation A output is finite", "a_result": "FAIL", "b_result": "NOT_RUN"})
        if not _finite(b_out):
            failures.append({"input": case, "assertion": "implementation B output is finite", "a_result": "PASS", "b_result": "FAIL"})
        if not harness.compare_outputs(a_out, b_out, rtol=RTOL, atol=ATOL, mode="allclose"):
            failures.append({"input": case, "assertion": "A and B outputs are allclose", "a_output": str(a_out), "b_output": str(b_out)})
    result = {
        "assertions_run": assertions_run,
        "failures": failures,
        "a_failures": sum(1 for f in failures if f.get("a_result") == "FAIL"),
        "b_failures": sum(1 for f in failures if f.get("b_result") == "FAIL"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
