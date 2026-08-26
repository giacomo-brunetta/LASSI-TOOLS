"""Interface shared by machine-specific compile checkers."""

# PyTorch is intentionally imported only inside the checker runtime.
# ruff: noqa: PLC0415, TC003

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any


class CheckerUnavailableError(RuntimeError):
    """The requested compiler environment is not installed or usable."""


class CompileChecker:
    """Base class for one target compiler implementation."""

    def __init__(self, target: dict[str, Any]) -> None:
        self.target = target
        self.options = dict(target.get("options") or {})

    def metadata(self) -> dict[str, Any]:
        return {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "checker": f"{type(self).__module__}:{type(self).__name__}",
        }

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
        raise NotImplementedError


def named_wrapper(module: Any, input_count: int) -> Any:
    """Wrap a varargs module with stable forward argument names for vendor SDKs."""
    import torch

    parameters = ", ".join(f"input{index}" for index in range(input_count))
    arguments = ", ".join(f"input{index}" for index in range(input_count))
    namespace: dict[str, Any] = {}
    exec(f"def forward(self, {parameters}):\n    return self.inner({arguments})\n", namespace)
    wrapper_type = type(
        "CompatibilityOpModule",
        (torch.nn.Module,),
        {"forward": namespace["forward"]},
    )
    wrapper = wrapper_type()
    wrapper.inner = module
    return wrapper.eval()
