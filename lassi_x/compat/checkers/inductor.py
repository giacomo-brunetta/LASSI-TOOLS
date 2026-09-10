"""Torch Inductor compile checker for CPU and CUDA targets."""

# PyTorch is imported only when this target checker is selected.
# ruff: noqa: PLC0415, TC003

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from lassi_x.compat.checkers.base import CheckerUnavailableError, CompileChecker, named_wrapper


class InductorChecker(CompileChecker):
    def metadata(self) -> dict[str, Any]:
        import torch

        metadata = super().metadata()
        device = str(self.options.get("device", "cuda:0"))
        metadata.update(
            {
                "torch": torch.__version__,
                "compiler": "torch-inductor",
                "device": device,
                "cuda_runtime": torch.version.cuda,
            }
        )
        if device.startswith("cuda"):
            if not torch.cuda.is_available():
                metadata["available"] = False
            else:
                index = torch.device(device).index or 0
                properties = torch.cuda.get_device_properties(index)
                metadata.update(
                    {
                        "available": True,
                        "device_name": properties.name,
                        "compute_capability": f"{properties.major}.{properties.minor}",
                    }
                )
        else:
            metadata["available"] = True
        return metadata

    def compile(
        self,
        module: Any,
        inputs: tuple[Any, ...],
        *,
        op_name: str,
        precision: str,
        case_hash: str,
        work_dir: Path,
    ) -> dict[str, Any]:
        del op_name, precision, case_hash, work_dir
        import torch

        device = str(self.options.get("device", "cuda:0"))
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise CheckerUnavailableError(f"configured CUDA device {device} is unavailable")
        wrapper = named_wrapper(module, len(inputs)).to(device)
        moved = tuple(
            value.to(device) if isinstance(value, torch.Tensor) else value for value in inputs
        )
        backend = str(self.options.get("backend", "inductor"))
        compiled = cast("Callable[..., Any]", torch.compile)(
            wrapper,
            backend=backend,
            fullgraph=bool(self.options.get("fullgraph", True)),
            dynamic=bool(self.options.get("dynamic", False)),
        )
        with torch.no_grad():
            compiled(*moved)  # Torch compilation is lazy; this is the compile trigger.
        if device.startswith("cuda"):
            torch.cuda.synchronize(device)
        return {
            "status": "compiled",
            "compile_trigger": "one untimed invocation",
            "backend": backend,
        }
