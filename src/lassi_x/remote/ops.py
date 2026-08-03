"""Workspace-confined execution and file operations shared by all backends.

These functions implement the semantics of the remote execution protocol
against one workspace root directory. :class:`~lassi_x.remote.agent.ExecutionAgent`
exposes them as Academy actions on a remote resource, and
:class:`~lassi_x.execution.LocalExecutionBackend` calls them directly so local
and remote execution stay behaviorally identical.

Every entry point re-validates path confinement against the resolved
filesystem, independent of the schema-level validation in
:mod:`lassi_x.protocol`, so a compromised or version-skewed peer cannot escape
the workspace root.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import os
import platform
import shutil
import socket
import subprocess
import time
from typing import TYPE_CHECKING, Literal

from lassi_x.protocol import (
    MAX_TEXT_BYTES,
    AcceleratorInfo,
    DirEntry,
    DirListing,
    ExecResult,
    FileContent,
    FileStat,
    HandshakeReport,
)

if TYPE_CHECKING:
    from pathlib import Path

    from lassi_x.protocol import ExecRequest, FileGet, FilePut, ListDir

_TOOLCHAIN_PROBES = ("gcc", "g++", "clang", "nvcc", "icpx", "make", "cmake")


def resolve_workspace(root: Path, workspace: str) -> Path:
    """Resolve and create the confined directory for one workspace name.

    Args:
        root: Workspace root directory owned by the executing side.
        workspace: Validated workspace identifier from a wire message.

    Returns:
        The workspace directory, created if necessary.

    Raises:
        ValueError: If the resolved directory would escape the workspace root.

    """
    base = root.resolve()
    path = (base / workspace).resolve()
    if path.parent != base:
        raise ValueError(f"workspace {workspace!r} escapes the workspace root")
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_member(workspace_dir: Path, relative: str) -> Path:
    """Resolve one workspace-relative path and enforce confinement.

    Args:
        workspace_dir: Resolved workspace directory.
        relative: Validated workspace-relative POSIX path from a wire message.

    Returns:
        The absolute path inside the workspace.

    Raises:
        ValueError: If the resolved path (following symlinks) leaves the workspace.

    """
    base = workspace_dir.resolve()
    path = (base / relative).resolve()
    if path != base and not path.is_relative_to(base):
        raise ValueError(f"path {relative!r} escapes the workspace")
    return path


def _clip(data: bytes) -> tuple[str, bool]:
    """Decode and truncate one output stream for inline transport.

    Args:
        data: Raw captured stream bytes.

    Returns:
        The decoded excerpt and whether the stream was truncated.

    """
    truncated = len(data) > MAX_TEXT_BYTES
    return data[:MAX_TEXT_BYTES].decode(errors="replace"), truncated


async def run_exec(root: Path, request: ExecRequest) -> ExecResult:
    """Execute one argv command inside its confined workspace.

    Launch failures (missing executable, permission errors) are reported as an
    :class:`ExecResult` with a ``None`` exit code rather than an exception, so
    they cross process and network boundaries as ordinary protocol data.

    Args:
        root: Workspace root directory owned by the executing side.
        request: Validated execution request.

    Returns:
        The command outcome with clipped output streams.

    Raises:
        ValueError: If the working directory escapes the workspace.

    """
    workspace_dir = resolve_workspace(root, request.workspace)
    cwd = workspace_dir if request.cwd is None else resolve_member(workspace_dir, request.cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(request.env)
    stdin_data = request.stdin_text.encode() if request.stdin_text is not None else None
    started = time.monotonic()
    try:
        process = await asyncio.create_subprocess_exec(
            *request.argv,
            cwd=cwd,
            env=env,
            stdin=asyncio.subprocess.PIPE if stdin_data is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        return ExecResult(
            workspace=request.workspace,
            exit_code=None,
            stderr=f"failed to launch {request.argv[0]!r}: {exc}",
            duration_s=time.monotonic() - started,
        )
    try:
        stdout_data, stderr_data = await asyncio.wait_for(
            process.communicate(stdin_data), timeout=request.timeout_s
        )
        timed_out = False
    except TimeoutError:
        process.kill()
        await process.wait()
        stdout_data, stderr_data = b"", b""
        timed_out = True
    stdout, stdout_truncated = _clip(stdout_data)
    stderr, stderr_truncated = _clip(stderr_data)
    return ExecResult(
        workspace=request.workspace,
        exit_code=None if timed_out else process.returncode,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        duration_s=time.monotonic() - started,
    )


def put_file(root: Path, request: FilePut) -> FileStat:
    """Write one file into its confined workspace.

    Args:
        root: Workspace root directory owned by the executing side.
        request: Validated write request carrying exactly one payload form.

    Returns:
        Digest and size of the bytes written.

    Raises:
        ValueError: If the destination escapes the workspace, the base64
            payload is malformed, or the payload digest does not match
            ``request.sha256``.
        FileNotFoundError: If the parent directory is missing and
            ``make_parents`` is disabled.

    """
    workspace_dir = resolve_workspace(root, request.workspace)
    path = resolve_member(workspace_dir, request.path)
    if request.text is not None:
        data = request.text.encode()
    else:
        assert request.content_b64 is not None  # guaranteed by model validation
        try:
            data = base64.b64decode(request.content_b64, validate=True)
        except binascii.Error as exc:
            raise ValueError(f"malformed base64 payload for {request.path!r}") from exc
    digest = hashlib.sha256(data).hexdigest()
    if request.sha256 is not None and digest != request.sha256:
        raise ValueError(f"payload digest mismatch for {request.path!r}")
    if request.make_parents:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if request.executable:
        path.chmod(path.stat().st_mode | 0o111)
    return FileStat(
        workspace=request.workspace,
        path=request.path,
        sha256=digest,
        size_bytes=len(data),
    )


def get_file(root: Path, request: FileGet) -> FileContent:
    """Read one file from its confined workspace.

    The returned ``sha256`` and ``size_bytes`` describe the transferred bytes,
    which cover the whole file unless ``truncated`` is set.

    Args:
        root: Workspace root directory owned by the executing side.
        request: Validated read request.

    Returns:
        The payload as UTF-8 text when possible, otherwise base64.

    Raises:
        ValueError: If the source escapes the workspace.
        OSError: If the file cannot be read.

    """
    workspace_dir = resolve_workspace(root, request.workspace)
    path = resolve_member(workspace_dir, request.path)
    size = path.stat().st_size
    with path.open("rb") as stream:
        data = stream.read(request.max_bytes)
    truncated = size > len(data)
    try:
        content = data.decode()
        encoding: Literal["utf-8", "base64"] = "utf-8"
    except UnicodeDecodeError:
        content = base64.b64encode(data).decode()
        encoding = "base64"
    return FileContent(
        workspace=request.workspace,
        path=request.path,
        encoding=encoding,
        content=content,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        truncated=truncated,
    )


def list_dir(root: Path, request: ListDir) -> DirListing:
    """List one directory inside its confined workspace.

    Args:
        root: Workspace root directory owned by the executing side.
        request: Validated listing request.

    Returns:
        Sorted entries with file sizes.

    Raises:
        ValueError: If the directory escapes the workspace.
        OSError: If the directory cannot be read.

    """
    workspace_dir = resolve_workspace(root, request.workspace)
    path = resolve_member(workspace_dir, request.path)
    entries = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.is_symlink() or not (child.is_file() or child.is_dir()):
            kind: Literal["file", "dir", "other"] = "other"
        elif child.is_dir():
            kind = "dir"
        else:
            kind = "file"
        entries.append(
            DirEntry(
                name=child.name,
                kind=kind,
                size_bytes=child.stat().st_size if kind == "file" else None,
            )
        )
    return DirListing(workspace=request.workspace, path=request.path, entries=entries)


def _probe_toolchain() -> dict[str, str]:
    """Report the first version line of each compiler or build tool on ``PATH``.

    Returns:
        Mapping of tool name to its reported version line.

    """
    toolchain: dict[str, str] = {}
    for tool in _TOOLCHAIN_PROBES:
        executable = shutil.which(tool)
        if executable is None:
            continue
        try:
            probe = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        first_line = (probe.stdout or probe.stderr).strip().splitlines()
        if first_line:
            toolchain[tool] = first_line[0]
    return toolchain


def _probe_accelerators() -> tuple[str | None, list[AcceleratorInfo]]:
    """Observe the torch build and every visible accelerator device.

    Returns:
        The torch version (``None`` when torch is unavailable) and the
        detected devices.

    """
    try:
        import torch  # noqa: PLC0415  # heavy import deferred to handshake time
    except ImportError:
        return None, []
    accelerators = []
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            accelerators.append(
                AcceleratorInfo(
                    kind="cuda",
                    name=properties.name,
                    index=index,
                    total_memory_mb=int(properties.total_memory // (1024 * 1024)),
                )
            )
    xpu = getattr(torch, "xpu", None)
    if xpu is not None and xpu.is_available():
        for index in range(xpu.device_count()):
            accelerators.append(
                AcceleratorInfo(kind="xpu", name=xpu.get_device_name(index), index=index)
            )
    if torch.backends.mps.is_available():
        accelerators.append(AcceleratorInfo(kind="mps", name="Apple Metal", index=0))
    return torch.__version__, accelerators


async def build_handshake(root: Path, resource: str | None) -> HandshakeReport:
    """Measure the capabilities of the executing host.

    Args:
        root: Workspace root directory owned by the executing side.
        resource: Configured resource name this agent serves, if any.

    Returns:
        Observed host, interpreter, torch, accelerator, and toolchain facts.

    """
    from lassi_x import __version__  # noqa: PLC0415  # avoid import cycle at module load

    torch_version, accelerators = await asyncio.to_thread(_probe_accelerators)
    toolchain = await asyncio.to_thread(_probe_toolchain)
    return HandshakeReport(
        resource=resource,
        hostname=socket.gethostname(),
        platform=platform.platform(),
        python_version=platform.python_version(),
        lassi_x_version=__version__,
        torch_version=torch_version,
        accelerators=accelerators,
        toolchain=toolchain,
        workspace_root=str(root.resolve()),
    )
