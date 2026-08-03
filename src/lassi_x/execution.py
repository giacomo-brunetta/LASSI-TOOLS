"""Execution backends: one interface for local and Academy-remote work.

The harness and the MCP tool server both talk to an :class:`ExecutionBackend`.
:class:`LocalExecutionBackend` runs everything in-process against a local
directory, while :class:`AcademyExecutionBackend` forwards each call to an
:class:`~lassi_x.remote.agent.ExecutionAgent` handle living on an HPC
resource. Both share the operation semantics in :mod:`lassi_x.remote.ops`, so
switching a run between local and remote execution changes transport only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .remote import ops

if TYPE_CHECKING:
    from pathlib import Path

    from academy.handle import Handle

    from .protocol import (
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
    from .remote.agent import ExecutionAgent


class ExecutionBackend(ABC):
    """Workspace-confined execution and file operations on one resource."""

    @abstractmethod
    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined workspace."""

    @abstractmethod
    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined workspace."""

    @abstractmethod
    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined workspace."""

    @abstractmethod
    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined workspace."""

    @abstractmethod
    async def handshake(self) -> HandshakeReport:
        """Measure and report the executing host's capabilities."""


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


class AcademyExecutionBackend(ExecutionBackend):
    """Forward every operation to a remote ``ExecutionAgent`` handle."""

    def __init__(self, handle: Handle[ExecutionAgent]) -> None:
        """Configure the backend.

        Args:
            handle: Academy handle of a launched execution agent.

        """
        self.handle = handle

    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined remote workspace."""
        return await self.handle.execute(request)

    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined remote workspace."""
        return await self.handle.put_file(request)

    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined remote workspace."""
        return await self.handle.get_file(request)

    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined remote workspace."""
        return await self.handle.list_dir(request)

    async def handshake(self) -> HandshakeReport:
        """Measure and report the remote host's capabilities."""
        return await self.handle.handshake()
