"""Hardened container used to execute the graph and its agents.

The host launches one long-lived container with the selected project bound
read-write at `/workspace` and read-only at `/reference`. Specific files
inside the editable project can be overlaid read-only (e.g. the pipeline
config and reference source), and a config that lives outside the project is
mounted separately at `/run/lassi-graph-config.json`.

The container hosts the entire graph: `exec_graph` runs the inner
`graph_flow.py` invocation, which in turn talks to Claude in-process for
every agent. There is no per-agent container dispatch.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

import docker
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from docker.types import Mount

logger = logging.getLogger(__name__)

CONTAINER_WORKSPACE = Path("/workspace")
CONTAINER_REFERENCE = Path("/reference")
EXTERNAL_CONFIG_MOUNT = Path("/run/lassi-graph-config.json")
SETTINGS_MOUNT = "/run/claude-settings.json"
PYTHON_BIN = "/opt/lassi/.venv/bin/python"
DEFAULT_IMAGE = "lassi-graph:latest"

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
class AgentContainer:
    """One hardened container that hosts an entire graph run."""

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
    name_prefix: str = "lassi-graph"

    _client: docker.DockerClient = field(init=False, repr=False)
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

        self._client = docker.from_env()

    # ------------------------------------------------------------------ image

    def _ensure_image(self) -> None:
        # `graph_flow.py` runs from the copy baked into /opt/lassi, not from
        # the selected project mount. Always pass the build context through
        # Docker's cache before launching so local graph edits cannot be
        # silently ignored by an existing image.
        inspect = subprocess.run(
            ["docker", "image", "inspect", self.image],
            capture_output=True,
        )
        if not self.auto_build:
            if inspect.returncode == 0:
                return
            raise RuntimeError(f"Docker image {self.image!r} not present and auto_build=False")
        if self.repo_root is None:
            raise RuntimeError(
                f"cannot build image {self.image!r} without repo_root"
            )
        logger.info(
            "refreshing image %s from %s/graph/Dockerfile",
            self.image, self.repo_root,
        )
        cmd = [
            "docker", "build",
            "--quiet",
            "--build-arg", "REQUIREMENTS_FILE=requirements/requirements_graph.txt",
            "-f", "graph/Dockerfile",
            "-t", self.image,
            ".",
        ]
        result = subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            diagnostics = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"docker build failed (exit {result.returncode}):\n{diagnostics}"
            )
        logger.info("image ready: %s", self.image)

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

    async def exec_graph(self, args: list[str]) -> str:
        """Execute the complete graph inside the hardened container, streaming
        stdout/stderr to the host TTY as it arrives.

        We bypass `Container.exec_run(stream=True)` (which mixes streams in a
        way that's awkward to demux) and drive the low-level Docker API
        directly so we get separate stdout/stderr chunks and a final exit code.
        """
        if self._container is None:
            raise RuntimeError("AgentContainer not started; call .start() first")

        cmd = [PYTHON_BIN, "/opt/lassi/graph/graph_flow.py", *args]
        api = self._client.api
        exec_handle = api.exec_create(
            self._container.id,
            cmd=cmd,
            stdout=True,
            stderr=True,
            tty=False,
        )

        loop = asyncio.get_event_loop()
        stdout_buf: list[str] = []
        stderr_buf: list[str] = []

        def _drain() -> None:
            stream = api.exec_start(exec_handle["Id"], stream=True, demux=True)
            for chunk in stream:
                if not chunk:
                    continue
                out_chunk, err_chunk = chunk
                if out_chunk:
                    text = out_chunk.decode("utf-8", errors="replace")
                    stdout_buf.append(text)
                    print(text, end="", flush=True)
                if err_chunk:
                    text = err_chunk.decode("utf-8", errors="replace")
                    stderr_buf.append(text)
                    print(text, end="", file=os.sys.stderr, flush=True)

        await loop.run_in_executor(None, _drain)

        info = api.exec_inspect(exec_handle["Id"])
        exit_code = info.get("ExitCode", 0)
        stdout = "".join(stdout_buf)
        stderr = "".join(stderr_buf)
        if exit_code != 0:
            raise RuntimeError(
                f"graph container exited {exit_code}; last stderr:\n{stderr[-2000:]}"
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
