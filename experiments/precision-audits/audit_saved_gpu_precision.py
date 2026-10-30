"""Read-only MINI CPU dtype checks of original Terra and accepted GPU ports.

This does not establish GPU compiler behavior, LARGE accuracy, or performance.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import signal
from pathlib import Path

import torch

from lassi_x.precision_audit_worker import audit_forward

ROOT = Path(__file__).resolve().parents[2]


def expired(signum, frame):
    raise TimeoutError("MINI CPU dtype probe exceeded five seconds")


def main():
    signal.signal(signal.SIGALRM, expired)
    torch.set_num_threads(1)
    records = []
    for campaign in ("a100-terra-medium-20261010", "a100-luna-from-terra-20261013"):
        for path in sorted((ROOT / "runs" / campaign / "runs").glob("*/*/run.json")):
            saved = json.loads(path.read_text())
            groups = ["compatibility_candidates"]
            if campaign == "a100-terra-medium-20261010":
                groups.append("candidates")
            for group in groups:
                for candidate in saved.get(group, []):
                    if candidate["status"] != "ok":
                        continue
                    precisions = (
                        [candidate.get("target_precision")]
                        if group == "compatibility_candidates"
                        else ["fp16", "bf16"]
                    )
                    for precision in precisions:
                        if precision not in {"fp16", "bf16"}:
                            continue
                        result = {
                            "campaign": campaign,
                            "kernel": saved["kernel"],
                            "candidate": candidate["candidate_id"],
                            "precision": precision,
                            "group": group,
                            "module": candidate["module_path"],
                        }
                        try:
                            signal.alarm(5)
                            spec = importlib.util.spec_from_file_location(
                                "saved_audit", candidate["module_path"]
                            )
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            dtype = torch.float16 if precision == "fp16" else torch.bfloat16
                            kwargs = {"device": "cpu", "dtype": dtype}
                            if "dataset" in inspect.signature(module.build_inputs).parameters:
                                kwargs["dataset"] = "mini"
                            inputs = module.build_inputs(**kwargs)
                            report = audit_forward(module.make_model().eval(), inputs, dtype)
                            report["violation_count"] = len(report["violations"])
                            report["violations"] = report["violations"][:3]
                            result.update(
                                status="passed" if report["passed"] else "violation", audit=report
                            )
                        except Exception as exc:
                            result.update(status="unresolved", error=f"{type(exc).__name__}: {exc}")
                        finally:
                            signal.alarm(0)
                        records.append(result)
    print(
        json.dumps(
            {
                "scope": (
                    "Actual MINI CPU forward dtype audit, not GPU/LARGE certification. "
                    "Unresolved cases are not passes."
                ),
                "records": records,
            }
        )
    )


if __name__ == "__main__":
    main()
