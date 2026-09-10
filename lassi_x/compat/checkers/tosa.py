"""Torch-MLIR to TOSA compile checker."""

# Torch-MLIR is an optional, environment-specific compiler dependency.
# ruff: noqa: PLC0415, TC003

from __future__ import annotations

from pathlib import Path
from typing import Any

from lassi_x.compat.checkers.base import CheckerUnavailableError, CompileChecker


def _compiler_api() -> tuple[Any, Any]:
    try:
        import torch_mlir  # type: ignore[import-not-found]
    except ImportError as error:
        raise CheckerUnavailableError("torch-mlir is unavailable") from error

    compile_fn = getattr(torch_mlir, "compile", None)
    output_type = getattr(torch_mlir, "OutputType", None)
    if compile_fn is not None and output_type is not None:
        return compile_fn, output_type

    from torch_mlir import torchscript

    return torchscript.compile, torchscript.OutputType


class TosaChecker(CompileChecker):
    """Check whether a canonical operator lowers to the TOSA dialect."""

    def metadata(self) -> dict[str, Any]:
        metadata = super().metadata()
        try:
            import torch_mlir
        except ImportError:
            metadata.update({"compiler": "torch-mlir", "available": False})
            return metadata
        metadata.update(
            {
                "compiler": "torch-mlir",
                "compiler_version": getattr(torch_mlir, "__version__", "unknown"),
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
        import torch

        compile_fn, output_type = _compiler_api()
        scripted = torch.jit.trace(  # type: ignore[no-untyped-call]
            module, inputs, strict=False, check_trace=False
        )
        compile_fn(scripted, inputs, output_type=output_type.TOSA)
        return {"status": "compiled", "compiler": "torch-mlir", "output_type": "TOSA"}
