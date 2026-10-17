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
import os
from pathlib import Path
from typing import Any

import torch
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten


class TargetDtypeAudit(TorchDispatchMode):  # type: ignore[no-untyped-call]
    def __init__(
        self,
        dtype: torch.dtype,
        *,
        arithmetic_policy: str = "target_format_only",
        allowed_ops: tuple[str, ...] = (),
    ) -> None:
        super().__init__()  # type: ignore[no-untyped-call]
        self.dtype = dtype
        self.operations = 0
        self.violations: list[str] = []
        self.arithmetic_policy = arithmetic_policy
        self.allowed_ops = allowed_ops
        self.observed_dtypes: set[str] = set()
        self.wider_operations: list[dict[str, Any]] = []
        self.wider_compute = False

    def check(self, value: Any, label: str) -> None:
        for item in tree_flatten(value)[0]:
            if isinstance(item, torch.Tensor) and item.is_floating_point():
                self.observed_dtypes.add(str(item.dtype))
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
        inputs = [
            x
            for x in tree_flatten((args, kwargs))[0]
            if isinstance(x, torch.Tensor) and x.is_floating_point()
        ]
        if not target_cast and any(x.dtype != self.dtype for x in inputs):
            self.wider_compute = True
        approved_accumulation = (
            self.arithmetic_policy == "mixed"
            and str(func) in self.allowed_ops
            and str(func)
            in {"aten.sum.default", "aten.sum.dim_IntList", "aten.mm.dtype", "aten.bmm.dtype"}
            and bool(inputs)
            and all(x.dtype == self.dtype for x in inputs)
            and self.dtype in (torch.float16, torch.bfloat16)
        )
        if (
            "_local_scalar_dense" in str(func)
            and any(
                isinstance(x, torch.Tensor) and x.is_floating_point() for x in tree_flatten(args)[0]
            )
            and len(self.violations) < 20
        ):
            self.violations.append(f"{func}: floating tensor escaped to host scalar arithmetic")
        result = func(*args, **kwargs)
        outputs = [
            x
            for x in tree_flatten(result)[0]
            if isinstance(x, torch.Tensor) and x.is_floating_point()
        ]
        wider = [x for x in outputs if x.dtype != self.dtype]
        if wider:
            event = {
                "operation": str(func),
                "inputs": sorted({str(x.dtype) for x in inputs}),
                "outputs": sorted({str(x.dtype) for x in outputs}),
            }
            if event not in self.wider_operations and len(self.wider_operations) < 20:
                self.wider_operations.append(event)
            approved_accumulation = approved_accumulation and all(
                x.dtype == torch.float32 for x in wider
            )
            self.observed_dtypes.update(str(x.dtype) for x in outputs)
            if not approved_accumulation:
                self.wider_compute = True
                self.check(result, f"{func} output")
        else:
            self.check(result, f"{func} output")
        return result

    @property
    def arithmetic_class(self) -> str:
        if self.wider_compute:
            return "wider_compute"
        return "mixed_accumulation" if self.wider_operations else "target_only"


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
        audit = TargetDtypeAudit(
            self.dtype,
            arithmetic_policy=self.report.get("arithmetic_policy", "target_format_only"),
            allowed_ops=tuple(self.report.get("allowed_mixed_accumulation_ops", [])),
        )
        audit.check(inputs, "supplied inputs")
        self.report["forward_calls"] += 1
        try:
            with audit:
                output = self.inner(*inputs)
            audit.check(output, "forward output")
        finally:
            self.report["operations"] += audit.operations
            self.report["observed_tensor_dtypes"] = sorted(
                set(self.report.get("observed_tensor_dtypes", [])) | audit.observed_dtypes
            )
            for event in audit.wider_operations:
                if event not in self.report.setdefault("wider_operations", []):
                    self.report["wider_operations"].append(event)
            classes = {self.report.get("arithmetic_class"), audit.arithmetic_class}
            self.report["arithmetic_class"] = (
                "wider_compute"
                if "wider_compute" in classes
                else "mixed_accumulation"
                if "mixed_accumulation" in classes
                else "target_only"
            )
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
                baseline_model = baseline.make_model().to(args.device, dtype=torch.float32).eval()
                model.to(dtype=torch.float32)
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
                "protocol": "executed-dtype-v4",
                "arithmetic_policy": os.environ.get(
                    "LASSI_ARITHMETIC_POLICY", "target_format_only"
                ),
                "allowed_mixed_accumulation_ops": json.loads(
                    os.environ.get("LASSI_MIXED_ACCUMULATION_OPS", "[]")
                ),
                "arithmetic_class": "unverified",
                "input_contract": "frozen_baseline" if args.audit_baseline else "candidate_inputs",
                "input_reference_hash": hashlib.sha256(args.audit_baseline.read_bytes()).hexdigest()
                if args.audit_baseline
                else "",
                "implicit_accumulator_precision": "unverified",
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
                if args.audit_baseline:
                    # Evaluate identical supplied values, never a repair's alternative encoding.
                    module.build_inputs = original_loader(args.audit_baseline).build_inputs
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
            if args.precision == "fp32" and report["passed"]:
                report["arithmetic_class"] = "control"
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
