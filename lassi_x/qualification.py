"""Compiler-only whole-candidate qualification targets."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Literal

from .execution import RemoteCallTimeoutError, ResourceUnavailableError
from .execution.transfer import put_bytes
from .protocol import ExecRequest
from .validation import fixture_relative_path

if TYPE_CHECKING:
    from .config import CompileTargetConfig, RunConfig
    from .execution import ExecutionContext
    from .types import Candidate


@dataclass(frozen=True, slots=True)
class QualificationResult:
    candidate_id: str
    target_id: str
    precision: str
    required: bool
    status: Literal["compiled", "rejected", "unavailable", "timeout"]
    resource: str
    duration_s: float | None = None
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "compiled"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> QualificationResult:
        return cls(**value)


async def qualify_candidate(
    config: RunConfig,
    execution: ExecutionContext,
    candidate: Candidate,
    target: CompileTargetConfig,
    precision: str,
) -> QualificationResult:
    """Compile a complete candidate without making any latency claim."""

    resource = target.resource or execution.default_resource
    backend = execution.backend(target.resource)
    raw = f"q-{candidate.candidate_id}-{target.target_id}-{precision}"
    workspace = re.sub(r"[^A-Za-z0-9._-]", "-", raw)[:64]
    candidate_source = candidate.module_path.read_bytes()
    fixture = fixture_relative_path(config)
    argv = [
        target.python,
        "-m",
        "lassi_x.qualification_worker",
        "--module",
        "candidate.py",
        "--target",
        target.target_id,
        "--precision",
        precision,
        "--dataset",
        config.evaluation_dataset,
    ]
    fixture_source = (
        config.resolve_project_path(config.oracle.input_fixture).read_bytes()
        if fixture is not None and config.oracle.input_fixture is not None
        else None
    )
    try:
        await put_bytes(backend, workspace, "candidate.py", candidate_source)
        if fixture is not None and fixture_source is not None:
            await put_bytes(backend, workspace, fixture, fixture_source)
            argv.extend(["--fixture", fixture])
        result = await backend.execute(
            ExecRequest(workspace=workspace, argv=argv, timeout_s=target.timeout_s)
        )
    except RemoteCallTimeoutError as exc:
        return QualificationResult(
            candidate.candidate_id,
            target.target_id,
            precision,
            target.required,
            "timeout",
            resource,
            notes=str(exc),
        )
    except (ResourceUnavailableError, OSError) as exc:
        return QualificationResult(
            candidate.candidate_id,
            target.target_id,
            precision,
            target.required,
            "unavailable",
            resource,
            notes=str(exc),
        )
    if result.timed_out:
        return QualificationResult(
            candidate.candidate_id,
            target.target_id,
            precision,
            target.required,
            "timeout",
            resource,
            result.duration_s,
            "compiler qualification timed out",
        )
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        payload = {"status": "rejected", "error": (result.stderr or result.stdout)[-4000:]}
    status = str(payload.get("status") or "rejected")
    if status not in {"compiled", "rejected", "unavailable"}:
        status = "rejected"
    return QualificationResult(
        candidate.candidate_id,
        target.target_id,
        precision,
        target.required,
        status,  # type: ignore[arg-type]
        resource,
        result.duration_s,
        str(payload.get("error") or payload.get("result") or result.stderr)[-4000:],
    )
