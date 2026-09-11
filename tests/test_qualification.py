from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, cast

from lassi_x.config import RunConfig
from lassi_x.execution import ExecutionContext, LocalExecutionBackend, RemoteCallTimeoutError
from lassi_x.protocol import ExecRequest, ExecResult
from lassi_x.qualification import qualify_candidate
from lassi_x.qualification_worker import _target_path
from lassi_x.types import Candidate, Status

from .test_config import minimal_config

if TYPE_CHECKING:
    from pathlib import Path


class QualificationExecution(LocalExecutionBackend):
    def __init__(self, workspace_root: Path, payload: dict[str, object]) -> None:
        super().__init__(workspace_root, "local")
        self.payload = payload
        self.requests: list[ExecRequest] = []

    async def execute(self, request: ExecRequest) -> ExecResult:
        self.requests.append(request)
        return ExecResult(
            workspace=request.workspace,
            exit_code=0,
            stdout=json.dumps(self.payload),
            duration_s=2.5,
        )


class QualificationContext:
    default_resource = "local"

    def __init__(self, backend: QualificationExecution) -> None:
        self._backend = backend

    def backend(self, resource: str | None = None) -> QualificationExecution:
        del resource
        return self._backend


class TimedOutQualificationExecution(QualificationExecution):
    async def execute(self, request: ExecRequest) -> ExecResult:
        raise RemoteCallTimeoutError("execute", "compiler", request.workspace, 30.0)


def test_whole_model_qualification_is_recorded_without_latency(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["compatibility"] = {
        "compile_targets": [{"target_id": "torch-mlir-tosa", "precisions": ["fp32"]}]
    }
    config = RunConfig.model_validate(data)
    module = tmp_path / "candidate.py"
    module.write_text("def make_model(): pass\n")
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    backend = QualificationExecution(tmp_path / "remote", {"status": "compiled", "result": {}})
    context = cast("ExecutionContext", QualificationContext(backend))
    target = config.compatibility.compile_targets[0]

    result = asyncio.run(qualify_candidate(config, context, candidate, target, "fp32"))

    assert result.passed
    assert result.status == "compiled"
    assert result.duration_s == 2.5
    assert "latency_s" not in result.to_dict()
    assert backend.requests[0].argv[1:3] == ["-m", "lassi_x.qualification_worker"]
    assert _target_path("torch-mlir-tosa").is_file()


def test_remote_qualification_timeout_does_not_abort_the_pipeline(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["compatibility"] = {
        "compile_targets": [{"target_id": "torch-mlir-tosa", "precisions": ["fp32"]}]
    }
    config = RunConfig.model_validate(data)
    module = tmp_path / "candidate.py"
    module.write_text("def make_model(): pass\n")
    candidate = Candidate("c1", "model", None, "direct", module, status=Status.OK)
    backend = TimedOutQualificationExecution(tmp_path / "remote", {})
    context = cast("ExecutionContext", QualificationContext(backend))

    result = asyncio.run(
        qualify_candidate(
            config,
            context,
            candidate,
            config.compatibility.compile_targets[0],
            "fp32",
        )
    )

    assert result.status == "timeout"
    assert not result.passed
    assert "unreachable" in result.notes
