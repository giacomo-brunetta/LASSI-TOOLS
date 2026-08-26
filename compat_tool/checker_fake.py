"""Deterministic checker used by framework tests and dry development runs."""

# ruff: noqa: TC003

from __future__ import annotations

from pathlib import Path
from typing import Any

from compat_tool.checker_base import CompileChecker


class FakeChecker(CompileChecker):
    def metadata(self) -> dict[str, Any]:
        return {**super().metadata(), "compiler": "fake", "available": True}

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
        del module, inputs, precision, case_hash, work_dir
        rejected = set(self.options.get("reject_ops") or [])
        if op_name in rejected:
            raise RuntimeError("synthetic compiler rejection")
        return {"status": "compiled", "compile_trigger": "fake checker"}
