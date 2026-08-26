"""GroqFlow compile checker."""

# Vendor modules must remain lazy so this package imports outside Groq environments.
# ruff: noqa: PLC0415, TC003

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from compat_tool.checker_base import CheckerUnavailableError, CompileChecker, named_wrapper


class GroqFlowChecker(CompileChecker):
    def _groqit(self) -> Any:
        try:
            from groqflow import groqit  # type: ignore[import-not-found]
        except ImportError as error:
            raise CheckerUnavailableError(f"groqflow is unavailable: {error}") from error
        return groqit

    def metadata(self) -> dict[str, Any]:
        import torch

        metadata = super().metadata()
        metadata.update(
            {
                "torch": torch.__version__,
                "compiler": "groqflow",
                "trace_dtype": str(self.options.get("trace_dtype", "float32")),
            }
        )
        try:
            import groqflow

            metadata["groqflow"] = getattr(groqflow, "__version__", "unknown")
            metadata["available"] = True
        except ImportError:
            metadata["available"] = False
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
        del precision, work_dir
        import torch

        groqit = self._groqit()
        trace_dtype = getattr(torch, str(self.options.get("trace_dtype", "float32")))
        traced_inputs = tuple(
            value.to(dtype=trace_dtype).contiguous()
            if isinstance(value, torch.Tensor) and value.is_floating_point()
            else value
            for value in inputs
        )
        wrapper = named_wrapper(module, len(traced_inputs))
        input_map = {f"input{index}": value for index, value in enumerate(traced_inputs)}
        build_name = re.sub(r"[^A-Za-z0-9._-]", "-", f"compat-{op_name}-{case_hash[:12]}")[:80]
        cache_dir = str(self.options.get("cache_dir", ".groq-compat-cache"))
        kwargs = {
            "build_name": build_name,
            "cache_dir": cache_dir,
            "rebuild": str(self.options.get("rebuild", "if_needed")),
        }
        try:
            groqit(wrapper, input_map, monitor=False, **kwargs)
        except TypeError:
            groqit(wrapper, input_map, **kwargs)
        return {
            "status": "compiled",
            "compile_trigger": "groqit returned a compiled model; no inference executed",
            "build_name": build_name,
            "trace_dtype": str(trace_dtype).removeprefix("torch."),
        }
