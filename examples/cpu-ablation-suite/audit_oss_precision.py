"""Read-only MINI CPU precision probes of accepted GPT-OSS translations.

The original experiment asked for FP64 CPU equivalence, not GPU precision repair.
These probes do not retroactively invalidate a valid FP64 translation score.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import signal
from pathlib import Path

import torch

from lassi_x.precision_audit_worker import AuditedModel

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "runs/cpu-gpt-oss-120b-openrouter-groq-medium-20261015"


def expired(signum, frame):
    raise TimeoutError("CPU precision probe exceeded five seconds")


def main() -> None:
    signal.signal(signal.SIGALRM, expired)
    torch.set_num_threads(1)
    records = []
    for entry in json.loads((ROOT / "suite.json").read_text())["entries"]:
        paths = sorted((ROOT / "runs" / entry["name"]).glob("*/run.json"))
        if not paths:
            continue
        saved = json.loads(paths[-1].read_text())
        for candidate in saved.get("candidates", []):
            if candidate["status"] != "ok":
                continue
            path = Path(candidate["module_path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            for precision, dtype in (
                ("fp32", torch.float32),
                ("fp16", torch.float16),
                ("bf16", torch.bfloat16),
            ):
                report = {"forward_calls": 0, "operations": 0, "violations": []}
                result = {
                    "kernel": entry["name"],
                    "candidate": candidate["candidate_id"],
                    "precision": precision,
                    "module": str(path),
                    "source_hash": digest,
                }
                try:
                    signal.alarm(5)
                    spec = importlib.util.spec_from_file_location("oss_precision_probe", path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    kwargs = {"device": "cpu", "dtype": dtype}
                    if "dataset" in inspect.signature(module.build_inputs).parameters:
                        kwargs["dataset"] = "mini"
                    inputs = module.build_inputs(**kwargs)
                    model = AuditedModel(module.make_model().eval(), dtype, report)
                    with torch.no_grad():
                        model(*inputs)
                    result["status"] = "passed_observed_cpu_dtype_probe"
                except Exception as exc:
                    result["status"] = "policy_violation" if report["violations"] else "unresolved"
                    result["error"] = f"{type(exc).__name__}: {exc}"
                finally:
                    signal.alarm(0)
                result["audit"] = report
                records.append(result)
    print(
        json.dumps(
            {
                "scope": (
                    "Accepted GPT-OSS FP64 CPU translations; exploratory MINI CPU dtype probes "
                    "at FP32/FP16/BF16. Not accuracy or GPU certification."
                ),
                "fp64_translation_results_modified": False,
                "model_calls": 0,
                "records": records,
            }
        )
    )


if __name__ == "__main__":
    main()
