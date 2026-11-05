"""Frozen-campaign capability probe for an unchanged historical Torch model.

This stage establishes extraction support only, with no candidate execution,
model calls, numerical qualification, or accelerator allocation.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from lassi_x import herbie
from lassi_x.campaign import Check, StageContext, Verdict


def main() -> None:
    context = StageContext.load()
    source = context.input_path("candidate")
    specification = json.loads(context.input_path("specification").read_text())
    frozen = context.input_path("herbie_adapter").read_bytes()
    actual = Path(herbie.__file__).read_bytes()
    if hashlib.sha256(frozen).digest() != hashlib.sha256(actual).digest():
        raise ValueError("Installed Herbie adapter differs from the frozen implementation")
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != specification["source_sha256"]:
        raise ValueError("Candidate differs from the declared archived source")
    tree = ast.parse(data.decode())
    cls = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == specification["class_name"]
    )
    try:
        herbie.extract(data.decode(), specification["class_name"], specification["precision"])
        status, reason = "passed", "The unchanged forward is supported by extraction"
    except herbie.UnsupportedExpressionError as exc:
        status, reason = "failed", str(exc)
    evidence = {
        **specification,
        "outcome": "supported" if status == "passed" else "unsupported",
        "reason": reason,
        "class_bases": [ast.unparse(base) for base in cls.bases],
        "methods": [n.name for n in cls.body if isinstance(n, ast.FunctionDef)],
        "calls": sorted({ast.unparse(n.func) for n in ast.walk(cls) if isinstance(n, ast.Call)}),
        "herbie_invocations": 0,
        "torch_forward_invocations": 0,
        "model_calls": 0,
        "numerically_validated": False,
        "target_validated": False,
        "precision_verified": False,
        "repaired": False,
    }
    (Path(context.work_dir) / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    context.finish(
        Verdict(
            status="passed" if status == "passed" else "failed",
            reason=reason,
            checks=[
                Check(
                    id="frozen-inputs", status="passed", reason="Source and adapter hashes verified"
                ),
                Check(
                    id="extraction-support",
                    status="passed" if status == "passed" else "failed",
                    reason=reason,
                ),
            ],
        )
    )


if __name__ == "__main__":
    main()
