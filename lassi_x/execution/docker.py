"""Disposable CPU containers for agent commands and candidate execution."""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from ..protocol import ExecRequest, HandshakeReport
from ..remote import ops
from .local import LocalExecutionBackend

if TYPE_CHECKING:
    from ..config import DockerExecutionConfig
    from ..protocol import ExecResult

ALLOWED_ENV = {"OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"}


class DockerExecutionBackend(LocalExecutionBackend):
    """Keep file transfer on the host; execute untrusted commands only in containers."""

    def __init__(
        self, workspace_root: Path, settings: DockerExecutionConfig, resource: str | None = "local"
    ) -> None:
        super().__init__(workspace_root, resource)
        self.settings = settings

    def command(self, request: ExecRequest, name: str) -> list[str]:
        """Build a fixed security policy; agents cannot supply Docker options."""
        if os.name != "posix" or os.getuid() == 0:
            raise ValueError("Docker CPU execution requires a non-root macOS/Linux host user")
        unknown = set(request.env) - ALLOWED_ENV
        if unknown:
            raise ValueError(f"Docker execution rejects environment variables: {sorted(unknown)}")
        workspace = ops.resolve_workspace(self.workspace_root, request.workspace)
        cwd = workspace if request.cwd is None else ops.resolve_member(workspace, request.cwd)
        cwd.mkdir(parents=True, exist_ok=True)
        if "," in str(workspace):
            raise ValueError("Docker workspace paths must not contain commas")
        validating = request.argv[:3] == ["/usr/local/bin/python", "-m", "lassi_x.runner"]
        memory = f"{self.settings.memory_mb}m"
        command = [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--name",
            name,
            "--init",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--cpus",
            str(self.settings.cpus),
            "--memory",
            memory,
            "--memory-swap",
            memory,
            "--pids-limit",
            str(self.settings.pids_limit),
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=256m,mode=1777",
            "--workdir",
            str(Path("/workspace") / cwd.relative_to(workspace)),
            "--mount",
            f"type=bind,src={workspace},dst=/workspace" + (",readonly" if validating else ""),
        ]
        if validating:
            output = ops.resolve_member(workspace, ".lassi")
            output.mkdir(parents=True, exist_ok=True)
            command += ["--mount", f"type=bind,src={output},dst=/workspace/.lassi"]
        elif (workspace / "reference").exists():
            reference = ops.resolve_member(workspace, "reference")
            command += ["--mount", f"type=bind,src={reference},dst=/workspace/reference,readonly"]
        for key, value in {**dict.fromkeys(ALLOWED_ENV, "1"), **request.env}.items():
            command += ["--env", f"{key}={value}"]
        if request.stdin_text is not None:
            command += ["--interactive"]
        return command + [self.settings.image, *request.argv]

    async def _remove(self, name: str) -> None:
        """Killing the Docker client alone does not terminate its container."""
        process = await asyncio.create_subprocess_exec(
            "docker",
            "rm",
            "--force",
            name,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            if process.returncode and b"No such container" not in stderr:
                raise RuntimeError(
                    f"Docker cleanup failed for {name}: {stderr.decode(errors='replace')}"
                )
        except TimeoutError:
            process.kill()
            await process.wait()
            raise RuntimeError(f"Docker cleanup timed out; check container {name}") from None

    async def execute(self, request: ExecRequest) -> ExecResult:
        name = f"lassi-cpu-{uuid.uuid4().hex}"
        command = self.command(request, name)
        try:
            return await ops.run_exec(
                self.workspace_root, request.model_copy(update={"argv": command, "env": {}})
            )
        finally:
            # Clean up after normal exit, timeout, cancellation or failed client launch.
            await asyncio.shield(self._remove(name))

    async def handshake(self) -> HandshakeReport:
        result = await self.execute(
            ExecRequest(
                workspace="docker-probe",
                argv=["/usr/local/bin/python", "/opt/probe.py"],
                timeout_s=60,
            )
        )
        if not result.ok:
            raise RuntimeError(f"Docker CPU runtime unavailable: {result.stderr or result.stdout}")
        report = HandshakeReport.model_validate_json(result.stdout.strip())
        return report.model_copy(update={"resource": self.resource})
