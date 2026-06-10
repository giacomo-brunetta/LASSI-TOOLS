"""Hardened container used to execute the graph and its agents.

The host launches one long-lived container with the selected project bound
read-write at `/workspace` and read-only at `/reference`. Specific files
inside the editable project can be overlaid read-only (e.g. the pipeline
config and reference source), and a config that lives outside the project is
mounted separately at `/run/lassi-graph-config.json`.

The normal graph entrypoint executes the complete graph inside this container.
The agent-dispatch methods remain available for callers that only want to
delegate individual agents.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import docker
from docker.errors import APIError, ImageNotFound, NotFound
from docker.models.containers import Container
from docker.types import Mount

from agents import Agent

logger = logging.getLogger(__name__)

CONTAINER_WORKSPACE = Path("/workspace")
CONTAINER_REFERENCE = Path("/reference")
EXTERNAL_CONFIG_MOUNT = Path("/run/lassi-graph-config.json")
SETTINGS_MOUNT = "/run/claude-settings.json"
AGENT_RUNNER = "/opt/lassi/graph/agent_runner.py"
PYTHON_BIN = "/opt/lassi/.venv/bin/python"
DEFAULT_IMAGE = "lassi-graph:latest"
RESULT_SENTINEL = "__LASSI_RESULT__"

FORWARDED_ENV = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_SKIP_ANTHROPIC_AUTH",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "CLOUD_ML_REGION",
    "ANTHROPIC_VERTEX_PROJECT_ID",
)


@dataclass
class PathMapper:
    """Translate absolute host paths under `project_root` to /workspace paths.

    Paths registered with `add_external(host, container)` are mapped to a
    fixed container destination (used for the external config file, which
    lives outside the project tree).
    """

    project_root: Path
    container_root: Path = CONTAINER_WORKSPACE
    externals: dict[Path, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.project_root = self.project_root.resolve()

    def add_external(self, host: Path, container: Path) -> None:
        self.externals[host.resolve()] = container

    def to_container(self, p: Path) -> Path:
        if not p.is_absolute():
            return p
        resolved = p.resolve()
        if resolved in self.externals:
            return self.externals[resolved]
        try:
            rel = resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(
                f"path {resolved} is outside the project root {self.project_root}; "
                f"add it as a read-only overlay or place it under {self.project_root}"
            ) from exc
        return self.container_root / rel


def encode_value(value: Any, mapper: PathMapper) -> Any:
    """Recursively encode a payload value, translating Paths through `mapper`."""
    if isinstance(value, Path):
        return {"__type__": "Path", "value": str(mapper.to_container(value))}
    if isinstance(value, dict):
        return {k: encode_value(v, mapper) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode_value(x, mapper) for x in value]
    return value


def _parse_envelope(stdout: str) -> dict:
    for line in stdout.splitlines()[::-1]:
        line = line.strip()
        if line.startswith(RESULT_SENTINEL):
            return json.loads(line[len(RESULT_SENTINEL):])
    raise RuntimeError(
        f"agent runner did not emit a {RESULT_SENTINEL} envelope; raw stdout:\n{stdout}"
    )


@dataclass
class AgentContainer:
    """One hardened container for a graph run or delegated agent dispatches."""

    project_dir: Path
    reference_dir: Path | None = None
    image: str = DEFAULT_IMAGE
    settings_path: Path | None = None
    repo_root: Path | None = None  # used to build the image lazily
    auto_build: bool = True
    external_config: Path | None = None
    # Project-relative or absolute host paths to overlay read-only on top of
    # the rw project mount. The pipeline config is added automatically.
    read_only_overlays: list[Path] = field(default_factory=list)
    # Project-relative paths sourced from the immutable reference snapshot and
    # overlaid read-only at the corresponding /workspace path.
    reference_overlays: list[Path] = field(default_factory=list)
    extra_env: dict[str, str] = field(default_factory=dict)
    name_prefix: str = "lassi-graph-agents"

    _client: docker.DockerClient = field(init=False, repr=False)
    _mapper: PathMapper = field(init=False, repr=False)
    _container: Container | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.project_dir = self.project_dir.resolve()
        if self.reference_dir is None:
            self.reference_dir = self.project_dir
        else:
            self.reference_dir = self.reference_dir.resolve()
        if self.settings_path is not None:
            self.settings_path = self.settings_path.resolve()
        if self.repo_root is not None:
            self.repo_root = self.repo_root.resolve()
        if self.external_config is not None:
            self.external_config = self.external_config.resolve()

        normalized: list[Path] = []
        for path in self.read_only_overlays:
            p = Path(path)
            if not p.is_absolute():
                p = (self.project_dir / p).resolve()
            else:
                p = p.resolve()
            try:
                p.relative_to(self.project_dir)
            except ValueError as exc:
                raise ValueError(
                    f"read-only overlay {p} is outside project {self.project_dir}; "
                    f"pass it via external_config instead"
                ) from exc
            normalized.append(p)
        self.read_only_overlays = normalized
        normalized_reference_overlays: list[Path] = []
        for path in self.reference_overlays:
            rel = (
                Path(path)
                if not Path(path).is_absolute()
                else Path(path).resolve().relative_to(self.project_dir)
            )
            if ".." in rel.parts:
                raise ValueError(f"reference overlay must stay inside project: {path}")
            source = self.reference_dir / rel
            if not source.exists():
                raise ValueError(f"reference overlay source does not exist: {source}")
            normalized_reference_overlays.append(rel)
        self.reference_overlays = normalized_reference_overlays

        self._mapper = PathMapper(self.project_dir)
        if self.external_config is not None:
            self._mapper.add_external(self.external_config, EXTERNAL_CONFIG_MOUNT)
        self._client = docker.from_env()

    # ------------------------------------------------------------------ image

    def _ensure_image(self) -> None:
        try:
            self._client.images.get(self.image)
            return
        except ImageNotFound:
            pass
        if not self.auto_build:
            raise RuntimeError(f"Docker image {self.image!r} not present and auto_build=False")
        if self.repo_root is None:
            raise RuntimeError(
                f"cannot build image {self.image!r} without repo_root"
            )
        logger.info("building image %s from %s/graph/Dockerfile", self.image, self.repo_root)
        cmd = [
            "docker", "build",
            "--build-arg", "REQUIREMENTS_FILE=requirements/requirements_graph.txt",
            "-f", "graph/Dockerfile",
            "-t", self.image,
            ".",
        ]
        result = subprocess.run(cmd, cwd=str(self.repo_root))
        if result.returncode != 0:
            raise RuntimeError(f"docker build failed (exit {result.returncode})")

    # --------------------------------------------------------------- container

    def _build_mounts(self) -> list[Mount]:
        mounts = [
            Mount(
                target=str(CONTAINER_WORKSPACE),
                source=str(self.project_dir),
                type="bind",
                read_only=False,
            ),
            Mount(
                target=str(CONTAINER_REFERENCE),
                source=str(self.reference_dir),
                type="bind",
                read_only=True,
            ),
        ]
        # Read-only overlays on top of the rw project mount.
        for path in self.read_only_overlays:
            rel = path.relative_to(self.project_dir)
            mounts.append(
                Mount(
                    target=str(CONTAINER_WORKSPACE / rel),
                    source=str(path),
                    type="bind",
                    read_only=True,
                )
            )
        for rel in self.reference_overlays:
            mounts.append(
                Mount(
                    target=str(CONTAINER_WORKSPACE / rel),
                    source=str(self.reference_dir / rel),
                    type="bind",
                    read_only=True,
                )
            )
        if self.external_config is not None:
            mounts.append(
                Mount(
                    target=str(EXTERNAL_CONFIG_MOUNT),
                    source=str(self.external_config),
                    type="bind",
                    read_only=True,
                )
            )
        if self.settings_path is not None:
            mounts.append(
                Mount(
                    target=SETTINGS_MOUNT,
                    source=str(self.settings_path),
                    type="bind",
                    read_only=True,
                )
            )
        return mounts

    def _container_env(self) -> dict[str, str]:
        env = {
            "HOME": "/tmp/lassi-home",
            "CLAUDE_CONFIG_DIR": "/tmp/lassi-home/.claude",
            "PYTHONUNBUFFERED": "1",
            "LASSI_ARTIFACT_DIR": "/workspace/LASSI",
            "LASSI_GRAPH_IN_CONTAINER": "1",
            "LASSI_REFERENCE_ROOT": str(CONTAINER_REFERENCE),
        }
        for name in FORWARDED_ENV:
            val = os.environ.get(name)
            if val is not None:
                env[name] = val
        env.update(self.extra_env)
        return env

    def start(self) -> None:
        if self._container is not None:
            return
        self._ensure_image()
        name = f"{self.name_prefix}-{os.getpid()}-{int(time.time())}"
        try:
            user = f"{os.getuid()}:{os.getgid()}"
        except AttributeError:  # pragma: no cover - non-POSIX
            user = None
        logger.info(
            "starting agent container %s (image=%s, project=%s, read-only overlays=%d)",
            name, self.image, self.project_dir, len(self.read_only_overlays),
        )
        self._container = self._client.containers.run(
            image=self.image,
            command=[
                "/opt/lassi/graph/docker_entrypoint.sh",
                "sleep", "infinity",
            ],
            name=name,
            detach=True,
            auto_remove=False,
            init=True,
            read_only=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            pids_limit=512,
            tmpfs={
                "/tmp": "rw,nosuid,nodev,size=2g,mode=1777",
                "/lassi-build": "rw,exec,nosuid,nodev,size=2g,mode=1777",
            },
            mounts=self._build_mounts(),
            environment=self._container_env(),
            working_dir=str(CONTAINER_WORKSPACE),
            user=user,
        )

    # ----------------------------------------------------------------- dispatch

    def _encode_payload(
        self,
        *,
        cwd: Path,
        allowed_paths: list[Path] | None,
        model: str | None,
        permission_mode: str,
        context: dict[str, Any],
    ) -> str:
        container_cwd = (
            self._mapper.to_container(cwd) if cwd.is_absolute() else CONTAINER_WORKSPACE
        )
        translated_allowed: list[dict] | None = None
        if allowed_paths is not None:
            translated_allowed = [encode_value(p, self._mapper) for p in allowed_paths]

        payload = {
            "cwd": {"__type__": "Path", "value": str(container_cwd)},
            "allowed_paths": translated_allowed,
            "model": model,
            "permission_mode": permission_mode,
            "context": encode_value(context, self._mapper),
        }
        return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")

    async def dispatch(self, agent: Agent, **kwargs: Any) -> str:
        if self._container is None:
            raise RuntimeError("AgentContainer not started; call .start() first")

        cwd: Path = kwargs.pop("cwd")
        allowed_paths: list[Path] | None = kwargs.pop("allowed_paths", None)
        model: str | None = kwargs.pop("model", None)
        permission_mode: str = kwargs.pop("permission_mode", "acceptEdits")

        payload_b64 = self._encode_payload(
            cwd=cwd,
            allowed_paths=allowed_paths,
            model=model,
            permission_mode=permission_mode,
            context=kwargs,
        )

        cmd = [
            PYTHON_BIN, AGENT_RUNNER,
            "--agent", agent.name,
            "--payload-b64", payload_b64,
        ]
        logger.info(
            "exec'ing agent '%s' in %s (payload=%d bytes)",
            agent.name, self._container.name, len(payload_b64),
        )

        loop = asyncio.get_event_loop()
        exec_result = await loop.run_in_executor(
            None,
            lambda: self._container.exec_run(
                cmd=cmd, demux=True, stdout=True, stderr=True,
            ),
        )

        exit_code = exec_result.exit_code
        stdout_raw, stderr_raw = exec_result.output or (b"", b"")
        stdout = (stdout_raw or b"").decode("utf-8", errors="replace")
        stderr = (stderr_raw or b"").decode("utf-8", errors="replace")

        if stderr.strip():
            for line in stderr.rstrip().splitlines():
                logger.info("[%s] %s", agent.name, line)

        try:
            envelope = _parse_envelope(stdout)
        except RuntimeError:
            raise RuntimeError(
                f"agent '{agent.name}' produced no parsable envelope "
                f"(exit={exit_code}); stderr was:\n{stderr}"
            )

        if not envelope.get("ok", False):
            raise RuntimeError(
                f"agent '{agent.name}' failed: {envelope.get('error', '<no error>')}"
            )
        return envelope["result"]

    async def exec_graph(self, args: list[str]) -> str:
        """Execute the complete graph inside the hardened container."""
        if self._container is None:
            raise RuntimeError("AgentContainer not started; call .start() first")

        cmd = [PYTHON_BIN, "/opt/lassi/graph/graph_flow.py", *args]
        loop = asyncio.get_event_loop()
        exec_result = await loop.run_in_executor(
            None,
            lambda: self._container.exec_run(
                cmd=cmd, demux=True, stdout=True, stderr=True,
            ),
        )
        stdout_raw, stderr_raw = exec_result.output or (b"", b"")
        stdout = (stdout_raw or b"").decode("utf-8", errors="replace")
        stderr = (stderr_raw or b"").decode("utf-8", errors="replace")
        if stderr:
            print(stderr, end="", file=os.sys.stderr)
        if stdout:
            print(stdout, end="")
        if exec_result.exit_code != 0:
            raise RuntimeError(
                f"graph container exited {exec_result.exit_code}; stderr:\n{stderr}"
            )
        return stdout

    # --------------------------------------------------------------- lifecycle

    def stop(self) -> None:
        if self._container is None:
            return
        logger.info("stopping agent container %s", self._container.name)
        with suppress(APIError, NotFound):
            self._container.kill(signal="SIGTERM")
        with suppress(APIError, NotFound):
            self._container.wait(timeout=5)
        with suppress(APIError, NotFound):
            self._container.remove(force=True)
        self._container = None

    def __enter__(self) -> "AgentContainer":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()


def make_backend(container: AgentContainer):
    """Adapter turning the container into a dispatch backend callable."""

    async def docker_dispatch_backend(agent: Agent, **kwargs):
        return await container.dispatch(agent, **kwargs)

    return docker_dispatch_backend
