"""Bounded, integrity-checked workspace file transfer."""

from __future__ import annotations

import base64
import hashlib
import uuid
from typing import TYPE_CHECKING

from ..protocol import MAX_INLINE_BYTES, ExecRequest, FileGet, FilePut

if TYPE_CHECKING:
    from .base import ExecutionBackend

TRANSFER_CHUNK_BYTES = 128 * 1024

_ASSEMBLE_CHUNKS = """\
import hashlib
import os
from pathlib import Path
import sys

destination = Path(sys.argv[1])
temporary = Path(sys.argv[2])
expected_digest = sys.argv[3]
parts = [Path(value) for value in sys.argv[4:]]
destination.parent.mkdir(parents=True, exist_ok=True)
digest = hashlib.sha256()
with temporary.open("wb") as output:
    for part in parts:
        data = part.read_bytes()
        digest.update(data)
        output.write(data)
if digest.hexdigest() != expected_digest:
    temporary.unlink(missing_ok=True)
    raise RuntimeError("assembled file digest mismatch")
os.replace(temporary, destination)
for part in parts:
    part.unlink()
parts[0].parent.rmdir()
"""


async def fetch_bytes(
    backend: ExecutionBackend,
    workspace: str,
    path: str,
    *,
    chunk_size: int | None = None,
) -> bytes:
    """Fetch one workspace file of any size through chunked reads.

    Args:
        backend: Backend serving the workspace.
        workspace: Workspace identifier.
        path: Workspace-relative file path.
        chunk_size: Maximum bytes per read; defaults to the inline limit.

    Returns:
        The complete file content.

    Raises:
        ValueError: If the path escapes the workspace.
        OSError: If the file cannot be read on the executing side.

    """
    chunks: list[bytes] = []
    offset = 0
    while True:
        content = await backend.get_file(
            FileGet(
                workspace=workspace,
                path=path,
                offset=offset,
                max_bytes=chunk_size or MAX_INLINE_BYTES,
            )
        )
        data = (
            base64.b64decode(content.content)
            if content.encoding == "base64"
            else content.content.encode()
        )
        chunks.append(data)
        offset += len(data)
        if not content.truncated:
            return b"".join(chunks)


async def put_bytes(
    backend: ExecutionBackend,
    workspace: str,
    path: str,
    data: bytes,
    *,
    chunk_size: int = TRANSFER_CHUNK_BYTES,
) -> None:
    """Stage bytes through bounded messages and atomically assemble large files.

    Args:
        backend: Backend serving the destination workspace.
        workspace: Workspace identifier.
        path: Workspace-relative destination path.
        data: Complete file payload.
        chunk_size: Maximum raw bytes carried by one message.

    Raises:
        ValueError: If ``path`` is unsafe or ``chunk_size`` is not positive.
        OSError: If remote chunk assembly or integrity verification fails.

    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    # Validate the final path with the wire model even when it will only be
    # written by the assembly command.
    FilePut(workspace=workspace, path=path, content_b64="")
    digest = hashlib.sha256(data).hexdigest()
    if len(data) <= chunk_size:
        await backend.put_file(
            FilePut(
                workspace=workspace,
                path=path,
                content_b64=base64.b64encode(data).decode(),
                sha256=digest,
            )
        )
        return

    transfer_id = uuid.uuid4().hex
    part_dir = f".lassi-transfer-{transfer_id}"
    part_paths: list[str] = []
    for index, offset in enumerate(range(0, len(data), chunk_size)):
        chunk = data[offset : offset + chunk_size]
        part_path = f"{part_dir}/{index:08d}.part"
        part_paths.append(part_path)
        await backend.put_file(
            FilePut(
                workspace=workspace,
                path=part_path,
                content_b64=base64.b64encode(chunk).decode(),
                sha256=hashlib.sha256(chunk).hexdigest(),
            )
        )
    temporary = f"{part_dir}/assembled.tmp"
    handshake = await backend.cached_handshake()
    result = await backend.execute(
        ExecRequest(
            workspace=workspace,
            argv=[
                handshake.python_executable,
                "-c",
                _ASSEMBLE_CHUNKS,
                path,
                temporary,
                digest,
                *part_paths,
            ],
            timeout_s=600,
        )
    )
    if not result.ok:
        raise OSError(
            f"failed to assemble staged file {path!r}: {(result.stderr or result.stdout)[-2000:]}"
        )
