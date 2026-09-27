"""Executable preflights for site-native accelerator workers."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from ..protocol import ExecRequest

if TYPE_CHECKING:
    from ..config import RunConfig
    from .context import ExecutionContext


async def native_runtime_checks(
    config: RunConfig, context: ExecutionContext
) -> tuple[bool, dict[str, dict[str, Any]]]:
    """Require every configured native accelerator to run a minimal workload.

    A control-plane handshake runs under the endpoint's Python interpreter,
    which may differ from the accelerator worker's interpreter. Device
    discovery is also insufficient for V-IPUs: a malformed or incompatible
    IPUoF partition can enumerate while PopTorch fails when it loads an engine.
    This deliberately compiles and executes a tiny graph before a pipeline can
    consume model-generation time or an accelerator allocation.
    """
    reports: dict[str, dict[str, Any]] = {}
    ok = True
    for spec in config.measure.backends:
        if spec.type != "native":
            continue
        resource = spec.resource or context.default_resource
        workspace = f"doctor-native-{uuid.uuid4().hex[:16]}"
        if spec.architecture == "graphcore_ipu":
            argv = [
                str(spec.worker.python),
                "-c",
                (
                    "import torch, poptorch; "
                    "version = poptorch.ipuHardwareVersion(); "
                    "assert version > 0, 'no IPU hardware available'; "
                    "model = torch.nn.Sequential(torch.nn.Linear(4, 4), torch.nn.ReLU()).eval(); "
                    "inputs = torch.ones(1, 4); "
                    "executor = poptorch.inferenceModel(model); "
                    "executor.compile(inputs); "
                    "output = executor(inputs); "
                    "assert output.shape == (1, 4) and torch.isfinite(output).all(), "
                    "'invalid IPU output'; "
                    "print(f'graphcore_ipu_model_smoke_ok hardware_version={version}')"
                ),
            ]
        else:
            # Cerebras owns device acquisition in its site worker. Confirm the
            # configured interpreter is executable before scheduling work.
            argv = [str(spec.worker.python), "-c", "import sys; print(sys.executable)"]
        try:
            result = await context.backends[resource].execute(
                ExecRequest(workspace=workspace, argv=argv, timeout_s=min(spec.timeout_s, 120.0))
            )
            passed = bool(result.ok)
            detail = (result.stderr or result.stdout).strip()[-2000:]
        except Exception as exc:
            passed = False
            detail = f"{type(exc).__name__}: {exc}"
        reports[spec.name] = {
            "resource": resource,
            "architecture": spec.architecture,
            "ok": passed,
            "detail": detail or None,
        }
        ok = ok and passed
    return ok, reports
