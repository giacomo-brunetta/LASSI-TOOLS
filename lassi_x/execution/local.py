"""In-process workspace execution backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..remote import ops
from .base import ExecutionBackend

if TYPE_CHECKING:
    from pathlib import Path

    from ..protocol import (
        DirListing,
        ExecRequest,
        ExecResult,
        FileContent,
        FileGet,
        FilePut,
        FileStat,
        HandshakeReport,
        ListDir,
    )


class LocalExecutionBackend(ExecutionBackend):
    """Run every operation in-process against a local workspace root."""

    def __init__(self, workspace_root: Path, resource: str | None = None) -> None:
        """Configure the backend.

        Args:
            workspace_root: Directory beneath which all workspaces live.
            resource: Resource name reported in the handshake.

        """
        self.workspace_root = workspace_root
        self.resource = resource

    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined workspace."""
        return await ops.run_exec(self.workspace_root, request)

    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined workspace."""
        return ops.put_file(self.workspace_root, request)

    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined workspace."""
        return ops.get_file(self.workspace_root, request)

    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined workspace."""
        return ops.list_dir(self.workspace_root, request)

    async def handshake(self) -> HandshakeReport:
        """Measure and report this host's capabilities."""
        return await ops.build_handshake(self.workspace_root, self.resource)
