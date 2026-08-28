"""Graphcore PopTorch compile checker for compatibility probes."""

# PopTorch must remain a lazy import so the compatibility wiki is usable off-system.
# ruff: noqa: PLC0415

from __future__ import annotations

from pathlib import Path
from typing import Any

from compat_tool.checker_base import CheckerUnavailableError, CompileChecker, named_wrapper


class PopTorchChecker(CompileChecker):
    def _modules(self) -> tuple[Any, Any]:
        try:
            import poptorch
            import torch
        except ImportError as error:
            raise CheckerUnavailableError(f"PopTorch is unavailable: {error}") from error
        return torch, poptorch

    def metadata(self) -> dict[str, Any]:
        torch, poptorch = self._modules()
        metadata = super().metadata()
        metadata.update(
            {
                "torch": torch.__version__,
                "compiler": "poptorch",
                "poptorch": getattr(poptorch, "__version__", "unknown"),
                "available": True,
            }
        )
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
        _, poptorch = self._modules()
        options = poptorch.Options()
        cache_dir = self.options.get("cache_dir")
        if cache_dir:
            Path(str(cache_dir)).mkdir(parents=True, exist_ok=True)
            options.enableExecutableCaching(str(cache_dir))
        wrapper = named_wrapper(module, len(inputs)).eval()
        compiled = poptorch.inferenceModel(wrapper, options=options)
        try:
            compiled.compile(*inputs)
        finally:
            destroy = getattr(compiled, "destroy", None)
            if destroy is not None:
                destroy()
        return {
            "status": "compiled",
            "compile_trigger": "PopTorch inferenceModel.compile",
        }
