"""Academy agent exposing confined execution on one compute resource."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from academy.agent import Agent, action

from lassi_x.remote import ops

if TYPE_CHECKING:
    from lassi_x.protocol import (
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


class ExecutionAgent(Agent):
    """Serve workspace-confined exec and file actions for one resource.

    One agent is launched per configured resource (for example ``nvidia`` or
    ``xpu``) onto that resource's executor. All actions take and return
    :mod:`lassi_x.protocol` messages, and every path is confined beneath the
    agent's workspace root.
    """

    def __init__(self, workspace_root: str, resource: str | None = None) -> None:
        """Configure the agent for one resource.

        Args:
            workspace_root: Directory beneath which all workspaces live,
                passed as a string because the value crosses the launch
                boundary and paths are site-local.
            resource: Configured resource name reported in the handshake.

        """
        super().__init__()
        self.workspace_root = Path(workspace_root)
        self.resource = resource

    async def agent_on_startup(self) -> None:
        """Create the workspace root so a misconfigured mount fails at launch."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    @action
    async def handshake(self) -> HandshakeReport:
        """Measure and report this host's capabilities.

        Returns:
            Observed host, torch, accelerator, and toolchain facts.

        """
        return await ops.build_handshake(self.workspace_root, self.resource)

    @action
    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined workspace.

        Args:
            request: Validated execution request.

        Returns:
            The command outcome with clipped output streams.

        """
        return await ops.run_exec(self.workspace_root, request)

    @action
    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined workspace.

        Args:
            request: Validated write request.

        Returns:
            Digest and size of the bytes written.

        """
        return ops.put_file(self.workspace_root, request)

    @action
    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined workspace.

        Args:
            request: Validated read request.

        Returns:
            The file payload as UTF-8 text or base64.

        """
        return ops.get_file(self.workspace_root, request)

    @action
    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined workspace.

        Args:
            request: Validated listing request.

        Returns:
            Sorted entries with file sizes.

        """
        return ops.list_dir(self.workspace_root, request)
