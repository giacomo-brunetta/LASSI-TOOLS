"""Observed dtype audit bound to executed forwards and CUDA graph capture.

This is not a hostile-code sandbox or proof of an accelerator's accumulator format.
The harness stages this file so remote package upgrades are not required.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import inspect
import io
import json
from pathlib import Path
from typing import Any

import torch
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten


class TargetDtypeAudit(TorchDispatchMode):  # type: ignore[no-untyped-call]
    def __init__(self, dtype: torch.dtype) -> None:
        super().__init__()  # type: ignore[no-untyped-call]
        self.dtype = dtype
        self.operations = 0
        self.violations: list[str] = []

    def check(self, value: Any, label: str) -> None:
        for item in tree_flatten(value)[0]:
            if (
                isinstance(item, torch.Tensor)
                and (item.is_floating_point() or item.is_complex())
                and item.dtype != self.dtype
            ):
                message = f"{label}: {item.dtype}, required {self.dtype}"
                if message not in self.violations and len(self.violations) < 20:
                    self.violations.append(message)

    def __torch_dispatch__(self, func: Any, types: Any, args: Any = (), kwargs: Any = None) -> Any:
        kwargs = kwargs or {}
        self.operations += 1
        # Stored constants may be wider, but their only permitted forward use is
        # conversion to the target dtype. Output checks still reject upcasts.
        target_cast = func == torch.ops.aten._to_copy.default and kwargs.get("dtype") == self.dtype
        if not target_cast:
            self.check((args, kwargs), f"{func} input")
        if (
            "_local_scalar_dense" in str(func)
            and any(
                isinstance(x, torch.Tensor) and x.is_floating_point() for x in tree_flatten(args)[0]
            )
            and len(self.violations) < 20
        ):
            self.violations.append(f"{func}: floating tensor escaped to host scalar arithmetic")
        result = func(*args, **kwargs)
        self.check(result, f"{func} output")
        return result


def audit_forward(model: Any, inputs: Any, dtype: torch.dtype) -> dict[str, Any]:
    audit = TargetDtypeAudit(dtype)
    audit.check(inputs, "supplied inputs")
    with torch.no_grad(), audit:
        output = model(*inputs)
        audit.check(output, "forward output")
    return {
        "protocol": "observed-eager-dtype-v2",
        "operations": audit.operations,
        "passed": not audit.violations,
        "violations": audit.violations,
        "scope": "explicit tensor arithmetic; implicit hardware accumulation not certified",
        "constant_policy": "wide constants allowed; cast before arithmetic; unused buffers OK",
    }


class AuditedModel(torch.nn.Module):
    """Guard the actual worker model, not a separately constructed preflight copy."""

    def __init__(self, model: Any, dtype: torch.dtype, report: dict[str, Any]) -> None:
        super().__init__()
        self.inner = model
        # Normalize stored floating constants once, outside all measured forwards.
        # Do not normalize inputs: a build_inputs contract violation must be caught.
        self.inner.to(dtype=dtype)
        self.dtype = dtype
        self.report = report

    def forward(self, *inputs: Any) -> Any:
        audit = TargetDtypeAudit(self.dtype)
        audit.check(inputs, "supplied inputs")
        self.report["forward_calls"] += 1
        try:
            with audit:
                output = self.inner(*inputs)
            audit.check(output, "forward output")
        finally:
            self.report["operations"] += audit.operations
            for violation in audit.violations:
                if violation not in self.report["violations"]:
                    self.report["violations"].append(violation)
        if audit.violations:
            raise RuntimeError("precision policy: " + "; ".join(audit.violations))
        return output


def main() -> int:
    # Parse only the shared flags needed for a pre-timing audit.
    from lassi_x import measure_worker  # noqa: PLC0415
    from lassi_x.runner import PRECISIONS, load_module  # noqa: PLC0415

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--module", type=Path)
    parser.add_argument("--precision")
    parser.add_argument("--device")
    parser.add_argument("--dataset", default="default")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--audit-baseline", type=Path)
    args, _ = parser.parse_known_args()
    report: dict[str, Any] = {"passed": True, "skipped": "high-precision control"}
    source_hash = hashlib.sha256(args.module.read_bytes()).hexdigest()
    original_loader = measure_worker.load_module
    old_active = getattr(measure_worker, "_PRECISION_AUDIT_ACTIVE", False)
    measure_worker._PRECISION_AUDIT_ACTIVE = True
    try:
        if args.precision in {"fp16", "bf16"} and args.audit_baseline:
            torch.manual_seed(args.seed)
            module = load_module(args.module)
            kwargs = {"device": args.device, "dtype": PRECISIONS[args.precision]}
            signature = inspect.signature(module.build_inputs).parameters
            if "dataset" in signature:
                kwargs["dataset"] = args.dataset
            if args.fixture and "fixture" in signature:
                kwargs["fixture"] = args.fixture
            inputs = module.build_inputs(**kwargs)
            model = module.make_model().to(args.device).eval()
            report = {"passed": True, "violations": []}
            if args.audit_baseline:
                baseline = load_module(args.audit_baseline)
                baseline_model = baseline.make_model().to(args.device).eval()
                build_kwargs = {**kwargs, "dtype": torch.float32}
                baseline_inputs = baseline.build_inputs(**build_kwargs)
                with torch.no_grad():
                    for scale in (0.9, 1.1):
                        supplied = tuple(
                            x * scale if x.is_floating_point() else x.clone()
                            for x in baseline_inputs
                        )
                        reference = baseline_model(*(x.clone() for x in supplied))
                        actual = model(*(x.clone() for x in supplied))
                        reference_items = tree_flatten(reference)[0]
                        actual_items = tree_flatten(actual)[0]
                        if len(reference_items) != len(actual_items) or any(
                            a.shape != b.shape
                            or not torch.allclose(
                                a.float(), b.float(), rtol=1e-3, atol=1e-5, equal_nan=True
                            )
                            for a, b in zip(reference_items, actual_items, strict=True)
                        ):
                            report["passed"] = False
                            report["violations"].append(
                                "supplied-input FP32 semantics differ from frozen base"
                            )
                report["supplied_input_checks"] = 2
                del baseline, baseline_model, baseline_inputs, supplied, reference, actual
            del inputs, model, module
            if args.device.startswith("cuda"):
                torch.cuda.synchronize()
                torch.cuda.empty_cache()
            if not report["passed"]:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "phase": "precision_policy",
                            "error": str(report["violations"]),
                            "dtype_audit": report,
                        }
                    )
                )
                return 1
        capture = io.StringIO()
        if args.precision in {"fp32", "fp16", "bf16"}:
            report = {
                "protocol": "executed-dtype-v3",
                "source_hash": source_hash,
                "requested_precision": args.precision,
                "dataset": args.dataset,
                "device": args.device,
                "scope": "executed forwards/CUDA capture; implicit accumulation unverified",
                "passed": None,
                "complete": False,
                "violations": [],
                "operations": 0,
                "forward_calls": 0,
                "constant_policy": "stored constants normalized before execution; inputs unchanged",
            }

            def guarded_loader(path: Path) -> Any:
                module: Any = original_loader(path)
                factory = module.make_model
                module.make_model = lambda: AuditedModel(
                    factory(), PRECISIONS[args.precision], report
                )
                return module

            measure_worker.load_module = guarded_loader
        # Strip wrapper-only flags before delegating to the installed worker.
        if args.audit_baseline:
            import sys  # noqa: PLC0415

            index = sys.argv.index("--audit-baseline")
            del sys.argv[index : index + 2]
        with contextlib.redirect_stdout(capture):
            code = measure_worker.main()
        payload = json.loads(capture.getvalue().strip().splitlines()[-1])
        if args.precision in {"fp32", "fp16", "bf16"}:
            report["complete"] = code == 0 and report["forward_calls"] > 0
            report["passed"] = (
                False if report["violations"] else True if report["complete"] else None
            )
            if report["passed"] is False:
                payload.update(ok=False, phase="precision_policy", error=str(report["violations"]))
            elif "HigherOrderOperator" in str(payload.get("error", "")):
                payload["phase"] = "precision_audit_execution"
        payload["dtype_audit"] = report
        payload["source_hash"] = source_hash
        print(json.dumps(payload))
        return code
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "phase": "precision_audit_execution",
                    "error": f"{type(exc).__name__}: {exc}",
                    "dtype_audit": report,
                    "source_hash": source_hash,
                }
            )
        )
        return 1
    finally:
        measure_worker.load_module = original_loader
        measure_worker._PRECISION_AUDIT_ACTIVE = old_active


if __name__ == "__main__":
    raise SystemExit(main())
