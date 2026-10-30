"""Frozen campaign plans and explicit, evidence-bearing stage handoffs.

Stage commands implement the scientific work. This module owns orchestration,
provenance, attempt budgets and recovery, independently of the execution target.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

import yaml
from pydantic import Field, model_validator

from .artifacts import atomic_write, write_json
from .config import StrictModel

if TYPE_CHECKING:
    import argparse

Name = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")]
Outcome = Literal["passed", "failed", "incomplete"]


class Output(StrictModel):
    path: str
    role: Literal["candidate", "evidence", "data"]

    @model_validator(mode="after")
    def safe_path(self) -> Output:
        path = Path(self.path)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("output paths must be relative and remain inside the work directory")
        return self


class Task(StrictModel):
    id: Name
    case: Name
    stage: Literal["generate", "adapt", "validate", "repair", "measure", "audit", "report"]
    command: list[str] = Field(min_length=1)
    timeout_s: float = Field(gt=0, allow_inf_nan=False)
    max_attempts: int = Field(default=1, ge=1)
    required: bool = True
    checks: list[Name] = Field(min_length=1)
    # Outcome dependencies make branches explicit, including repairs of failed stages.
    dependencies: dict[Name, list[Outcome]] = Field(default_factory=dict)
    # Each value is either files/<name> or <task-id>/<output-name>.
    inputs: dict[Name, str] = Field(default_factory=dict)
    outputs: dict[Name, Output] = Field(min_length=1)


class Import(StrictModel):
    campaign: str
    task: Name
    attempt: int = Field(ge=1, le=999999)
    output: Name
    accept: list[Outcome] = Field(default=["passed"], min_length=1)


class Plan(StrictModel):
    schema_version: Literal[1] = 1
    name: Name
    methodology: str = Field(min_length=1)
    # Record workload profiles, gates, model budgets, selection rules and environment.
    protocol: dict[str, object] = Field(min_length=1)
    files: dict[Name, str | Import] = Field(default_factory=dict)
    tasks: list[Task] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_graph(self) -> Plan:
        tasks = {task.id: task for task in self.tasks}
        if len(tasks) != len(self.tasks) or "files" in tasks:
            raise ValueError("task IDs must be unique; 'files' is reserved")
        for task in self.tasks:
            if len(task.checks) != len(set(task.checks)):
                raise ValueError(f"duplicate checks in {task.id}")
            for argument in task.command:
                if (
                    argument.startswith("{input:")
                    and argument.endswith("}")
                    and argument[7:-1] not in task.inputs
                ):
                    raise ValueError(f"undeclared command input in {task.id}: {argument}")
            for dependency, outcomes in task.dependencies.items():
                if dependency not in tasks or not outcomes or len(outcomes) != len(set(outcomes)):
                    raise ValueError(f"invalid dependency in {task.id}: {dependency}")
            for reference in task.inputs.values():
                pieces = reference.split("/")
                if len(pieces) != 2:
                    raise ValueError(f"invalid artifact reference: {reference}")
                owner, name = pieces
                if owner == "files":
                    valid = name in self.files
                else:
                    valid = (
                        owner in task.dependencies
                        and owner in tasks
                        and name in tasks[owner].outputs
                    )
                if not valid:
                    raise ValueError(f"undeclared input: {reference}")
        self.ordered_tasks()  # Reject cycles before any filesystem changes.
        return self

    def ordered_tasks(self) -> list[Task]:
        ordered: list[Task] = []
        pending = list(self.tasks)
        while pending:
            ready = [task for task in pending if set(task.dependencies) <= {t.id for t in ordered}]
            if not ready:
                raise ValueError("campaign dependencies contain a cycle")
            ordered.extend(ready)
            pending = [task for task in pending if task not in ready]
        return ordered


class Check(StrictModel):
    id: Name
    status: Literal["passed", "failed", "not_run", "inconclusive"]
    reason: str = Field(min_length=1)


class Verdict(StrictModel):
    status: Outcome
    reason: str = Field(min_length=1)
    checks: list[Check] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self) -> Verdict:
        if len({check.id for check in self.checks}) != len(self.checks):
            raise ValueError("check IDs must be unique")
        statuses = {check.status for check in self.checks}
        if self.status == "passed" and statuses != {"passed"}:
            raise ValueError("a positive verdict requires every check to pass")
        if self.status == "failed" and "failed" not in statuses:
            raise ValueError("a failed verdict needs a failed check")
        return self


class Artifact(StrictModel):
    path: str
    sha256: str
    role: Literal["candidate", "evidence", "data"]
    parents: dict[str, str] = Field(default_factory=dict)


class Attempt(StrictModel):
    task: str
    number: int
    status: Outcome
    reason: str
    returncode: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    wall_seconds: float | None = None
    checks: list[Check] = Field(default_factory=list)
    inputs: dict[str, Artifact] = Field(default_factory=dict)
    outputs: dict[str, Artifact] = Field(default_factory=dict)


class Frozen(StrictModel):
    schema_version: Literal[1] = 1
    plan: Plan
    files: dict[str, Artifact]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(source: Path, root: Path) -> None:
    """Freeze a validated plan and copy its declared external inputs."""
    plan = Plan.model_validate(yaml.safe_load(source.read_text()))
    contents: dict[str, tuple[bytes, Artifact]] = {}
    for name, item in plan.files.items():
        if isinstance(item, str):
            path = source.resolve().parent / item
            data = path.read_bytes()
            artifact = Artifact(path=path.name, sha256=digest(data), role="data")
        else:
            origin = Campaign(source.resolve().parent / item.campaign)
            origin_task = next((t for t in origin.frozen.plan.tasks if t.id == item.task), None)
            if origin_task is None:
                raise ValueError(f"unknown imported task: {item.task}")
            attempt = origin.record(origin_task, item.attempt)
            if attempt.status not in item.accept or item.output not in attempt.outputs:
                raise ValueError(f"imported artifact not eligible: {name}")
            artifact = attempt.outputs[item.output].model_copy(deep=True)
            data = origin.read_artifact(artifact)
            identity = (origin.root / "plan.sha256").read_text().strip()
            parent = f"{identity}/{item.task}/{item.attempt}/{item.output}"
            artifact.parents[parent] = artifact.sha256
        contents[name] = data, artifact
    root.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, (data, artifact) in contents.items():
        path = root / "files" / (name + Path(artifact.path).suffix)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        files[name] = artifact.model_copy(update={"path": str(path.relative_to(root))})
    frozen = Frozen(plan=plan, files=files)
    write_json(root / "plan.json", frozen.model_dump())
    (root / "plan.sha256").write_text(digest((root / "plan.json").read_bytes()) + "\n")


class Campaign:
    def __init__(self, root: Path):
        self.root = root.resolve()
        raw = (self.root / "plan.json").read_bytes()
        if digest(raw) != (self.root / "plan.sha256").read_text().strip():
            raise ValueError("frozen campaign plan changed; prepare a new campaign")
        self.frozen = Frozen.model_validate_json(raw)
        for artifact in self.frozen.files.values():
            self.read_artifact(artifact)

    def read_artifact(self, artifact: Artifact) -> bytes:
        path = (self.root / artifact.path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("artifact escapes campaign directory")
        data = path.read_bytes()
        if digest(data) != artifact.sha256:
            raise ValueError(f"artifact changed: {artifact.path}")
        return data

    def attempts(self, task: Task) -> list[Path]:
        directory = self.root / "tasks" / task.id
        attempts = sorted(directory.glob("[0-9][0-9][0-9][0-9][0-9][0-9]"))
        if any(path.name != f"{index:06d}" for index, path in enumerate(attempts, 1)):
            raise ValueError(f"attempt history has gaps for {task.id}")
        return attempts

    def latest(self, task: Task) -> Attempt | None:
        attempts = self.attempts(task)
        if not attempts:
            return None
        return self.record(task, len(attempts))

    def record(self, task: Task, number: int) -> Attempt:
        directory = self.root / "tasks" / task.id / f"{number:06d}"
        if not directory.is_dir():
            raise ValueError(f"attempt does not exist: {task.id}/{number}")
        result = directory / "result.json"
        checksum = directory / "result.sha256"
        if not result.exists() or not checksum.exists():
            return Attempt(
                task=task.id,
                number=number,
                status="incomplete",
                reason="Attempt has no terminal record; if interrupted, explicit retry is required",
                checks=[
                    Check(id=name, status="inconclusive", reason="No committed terminal evidence")
                    for name in task.checks
                ],
            )
        if digest(result.read_bytes()) != checksum.read_text().strip():
            raise ValueError(f"attempt record changed: {result}")
        attempt = Attempt.model_validate_json(result.read_bytes())
        if attempt.task != task.id or attempt.number != number:
            raise ValueError("attempt identity does not match its directory")
        for artifact in attempt.outputs.values():
            self.read_artifact(artifact)
        return attempt

    def inputs(self, task: Task) -> tuple[dict[str, Artifact], str | None]:
        records = {
            t.id: self.latest(t) for t in self.frozen.plan.tasks if t.id in task.dependencies
        }
        for dependency, accepted in task.dependencies.items():
            record = records[dependency]
            if record is None or record.status not in accepted:
                status = record.status if record else "not_run"
                return {}, f"Dependency {dependency} is {status}; requires {', '.join(accepted)}"
        inputs = {}
        for name, reference in task.inputs.items():
            owner, output = reference.split("/")
            if owner == "files":
                artifact = self.frozen.files[output]
            else:
                record = records[owner]
                if record is None or output not in record.outputs:
                    return {}, f"Required artifact {reference} was not produced"
                artifact = record.outputs[output]
            self.read_artifact(artifact)
            inputs[name] = artifact
        return inputs, None

    def summary(self) -> dict[str, object]:
        rows = []
        active_task = None
        with (self.root / ".lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                active = self.root / "active.json"
                if active.exists():
                    active_task = json.loads(active.read_text())["task"]
        for task in self.frozen.plan.tasks:
            record = self.latest(task)
            _, blocked = self.inputs(task)
            rows.append(
                {
                    "task": task.id,
                    "case": task.case,
                    "stage": task.stage,
                    "status": "running"
                    if active_task == task.id
                    else (record.status if record else ("blocked" if blocked else "not_run")),
                    "reason": record.reason if record else blocked,
                    "attempts": len(self.attempts(task)),
                    "history": [
                        {
                            "attempt": prior.number,
                            "status": prior.status,
                            "reason": prior.reason,
                            "checks": [check.model_dump() for check in prior.checks],
                        }
                        for number in range(1, len(self.attempts(task)) + 1)
                        for prior in [self.record(task, number)]
                    ],
                }
            )
        return {"name": self.frozen.plan.name, "tasks": rows}

    def run(self, retry: str | None = None) -> None:
        """Continue unstarted tasks; only an explicit retry repeats a terminal attempt."""
        with (self.root / ".lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("another runner is active for this campaign") from exc
            tasks = self.frozen.plan.ordered_tasks()
            if retry is not None:
                selected = next((t for t in tasks if t.id == retry), None)
                if selected is None:
                    raise ValueError(f"unknown task: {retry}")
                previous = self.latest(selected)
                if previous is None or previous.status == "passed":
                    raise ValueError("retry requires a failed or incomplete attempt")
                # A published downstream attempt must never silently acquire a new parent.
                descendants = {retry}
                for task in tasks:
                    if set(task.dependencies) & descendants:
                        descendants.add(task.id)
                        if self.attempts(task):
                            raise ValueError("downstream attempts exist; prepare a new campaign")
                try:
                    self.execute(selected)
                finally:
                    (self.root / "active.json").unlink(missing_ok=True)
            else:
                for task in tasks:
                    if self.latest(task) is None:
                        _, blocked = self.inputs(task)
                        if blocked is None:
                            try:
                                self.execute(task)
                            finally:
                                (self.root / "active.json").unlink(missing_ok=True)

    def execute(self, task: Task) -> None:
        inputs, blocked = self.inputs(task)
        if blocked:
            raise ValueError(blocked)
        number = len(self.attempts(task)) + 1
        if number > task.max_attempts or number > 999999:
            raise ValueError(f"attempt budget exhausted for {task.id}")
        directory = self.root / "tasks" / task.id / f"{number:06d}"
        directory.mkdir(parents=True, exist_ok=False)
        write_json(self.root / "active.json", {"task": task.id, "attempt": number})
        work = directory / "work"
        work.mkdir()
        copied = {}
        for name, artifact in inputs.items():
            path = directory / "inputs" / (name + Path(artifact.path).suffix)
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(self.read_artifact(artifact))
            copied[name] = {**artifact.model_dump(), "local_path": str(path)}
        context = directory / "context.json"
        write_json(
            context,
            {
                "schema_version": 1,
                "task": task.model_dump(),
                "attempt": number,
                "protocol": self.frozen.plan.protocol,
                "plan_sha256": (self.root / "plan.sha256").read_text().strip(),
                "inputs": copied,
                "work_dir": str(work),
                "verdict_path": str(work / "verdict.json"),
            },
        )
        result = Attempt(
            task=task.id,
            number=number,
            status="incomplete",
            reason="Stage did not finish",
            inputs=inputs,
            started_at=dt.datetime.now(dt.UTC).isoformat(),
        )
        started = time.monotonic()
        environment = {**os.environ, "LASSI_CAMPAIGN_CONTEXT": str(context)}
        command = []
        for argument in task.command:
            if argument.startswith("{input:") and argument.endswith("}"):
                name = argument[7:-1]
                if name not in copied:
                    raise ValueError(f"unknown command input: {name}")
                command.append(str(copied[name]["local_path"]))
            else:
                command.append(argument)
        try:
            with (
                (directory / "stdout.log").open("wb") as stdout,
                (directory / "stderr.log").open("wb") as stderr,
            ):
                process = subprocess.Popen(
                    command,
                    cwd=work,
                    env=environment,
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True,
                )
                try:
                    result.returncode = process.wait(timeout=task.timeout_s)
                except BaseException:
                    # Include child workers in timeout/interruption cleanup.
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
            verdict = Verdict.model_validate_json((work / "verdict.json").read_bytes())
            result.checks = verdict.checks
            reported = {check.id for check in verdict.checks}
            if reported != set(task.checks):
                result.checks.extend(
                    Check(id=name, status="not_run", reason="Stage omitted this planned check")
                    for name in task.checks
                    if name not in reported
                )
                raise ValueError("stage verdict does not cover exactly the planned checks")
            result.reason = verdict.reason
            result.status = verdict.status
            if result.returncode != 0:
                result.status = "incomplete"
                result.reason = f"Stage process exited {result.returncode}; {verdict.reason}"
            for name, output in task.outputs.items():
                source = (work / output.path).resolve()
                if not source.is_relative_to(work):
                    raise ValueError("output escapes work directory")
                if not source.is_file():
                    if result.status == "passed":
                        raise ValueError(f"passing stage omitted output {name}")
                    continue
                data = source.read_bytes()
                target = directory / "artifacts" / (name + source.suffix)
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(data)
                result.outputs[name] = Artifact(
                    path=str(target.relative_to(self.root)),
                    sha256=digest(data),
                    role=output.role,
                    parents={name: item.sha256 for name, item in inputs.items()},
                )
            # Stage commands must not alter their supplied input copies.
            for name, artifact in inputs.items():
                if digest(Path(str(copied[name]["local_path"])).read_bytes()) != artifact.sha256:
                    raise ValueError(f"stage modified input {name}")
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            result.status = "incomplete"
            result.reason = f"{type(exc).__name__}: {exc}"
        finally:
            result.finished_at = dt.datetime.now(dt.UTC).isoformat()
            result.wall_seconds = time.monotonic() - started
            reported = {check.id for check in result.checks}
            result.checks.extend(
                Check(id=name, status="inconclusive", reason=result.reason)
                for name in task.checks
                if name not in reported
            )
            write_json(directory / "result.json", result.model_dump())
            atomic_write(
                directory / "result.sha256", digest((directory / "result.json").read_bytes()) + "\n"
            )


class LocalInput(Artifact):
    local_path: str


class StageContext(StrictModel):
    """Interface used by trusted stage adapters; candidates never write verdicts."""

    schema_version: Literal[1] = 1
    task: Task
    attempt: int
    protocol: dict[str, object]
    plan_sha256: str
    inputs: dict[str, LocalInput]
    work_dir: str
    verdict_path: str

    @classmethod
    def load(cls) -> StageContext:
        return cls.model_validate_json(Path(os.environ["LASSI_CAMPAIGN_CONTEXT"]).read_bytes())

    def input_path(self, name: str) -> Path:
        artifact = self.inputs[name]
        path = Path(artifact.local_path)
        if digest(path.read_bytes()) != artifact.sha256:
            raise ValueError(f"input changed: {name}")
        return path

    def finish(self, verdict: Verdict) -> None:
        if {check.id for check in verdict.checks} != set(self.task.checks):
            raise ValueError("verdict must report every planned check exactly once")
        write_json(Path(self.verdict_path), verdict.model_dump())


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("campaign", help="Prepare and continue frozen campaigns")
    commands = parser.add_subparsers(dest="campaign_command", required=True)
    prepare_parser = commands.add_parser("prepare", help="Freeze a campaign plan and inputs")
    prepare_parser.add_argument("plan", type=Path)
    prepare_parser.add_argument("directory", type=Path)
    for name in ("run", "retry", "status"):
        command = commands.add_parser(name)
        command.add_argument("directory", type=Path)
        if name == "retry":
            command.add_argument("--task", required=True)
    parser.set_defaults(func=command_campaign)


def command_campaign(args: argparse.Namespace) -> int:
    try:
        if args.campaign_command == "prepare":
            prepare(args.plan, args.directory)
        campaign = Campaign(args.directory)
        if args.campaign_command in {"run", "retry"}:
            campaign.run(args.task if args.campaign_command == "retry" else None)
        summary = campaign.summary()
        print(json.dumps(summary, indent=2))
        if args.campaign_command in {"run", "retry"}:
            return int(
                any(
                    record is None or record.status != "passed"
                    for task in campaign.frozen.plan.tasks
                    if task.required
                    for record in [campaign.latest(task)]
                )
            )
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
