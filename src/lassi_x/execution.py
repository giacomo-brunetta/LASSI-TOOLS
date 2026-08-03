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
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from .remote import ops

if TYPE_CHECKING:
    from pathlib import Path

    from academy.handle import Handle

    from .config import RunConfig
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


class ExecutionContext:
    """Everything one run needs to fan tool calls out to its resources.

    Owns the execution backends (in-process or Academy-launched), the local
    MCP server the Hermes sessions connect to, and the per-workspace server
    entries registered in the Hermes configuration. Create it with
    :meth:`start` and always close it (or use ``async with``) so Hermes
    configuration entries and background services are cleaned up.
    """

    def __init__(
        self,
        *,
        backends: dict[str, ExecutionBackend],
        default_resource: str,
        workspace_roots: dict[str, Path],
        mcp_timeout_s: float,
        hermes_home: Path | None = None,
    ) -> None:
        """Wire the context; use :meth:`start` instead of calling this directly.

        Args:
            backends: Execution backends keyed by resource name.
            default_resource: Resource used when a request names none.
            workspace_roots: Local workspace root per resource, used to locate
                workspace files on the harness side.
            mcp_timeout_s: Per-tool-call timeout written into Hermes entries.
            hermes_home: Hermes home override for configuration registration.

        """
        from .mcp_server import LassiMCPServer, MCPServerRunner  # noqa: PLC0415

        self.backends = backends
        self.default_resource = default_resource
        self.workspace_roots = workspace_roots
        self.mcp_timeout_s = mcp_timeout_s
        self.hermes_home = hermes_home
        self.mcp = LassiMCPServer(backends, default_resource=default_resource)
        self.runner = MCPServerRunner(self.mcp)
        self.registered_servers: list[str] = []
        self._manager: object | None = None

    @classmethod
    async def start(
        cls,
        config: RunConfig,
        run_dir: Path,
        *,
        hermes_home: Path | None = None,
    ) -> ExecutionContext:
        """Build backends from configuration and start the MCP server.

        In ``academy`` mode one :class:`~lassi_x.remote.agent.ExecutionAgent`
        is launched per configured resource. Without an ``exchange_url`` the
        agents run through a local exchange on this machine; Globus Compute
        endpoints are wired in a later phase.

        Args:
            config: Validated run configuration.
            run_dir: Root artifact directory for the current pipeline run.
            hermes_home: Hermes home override for configuration registration.

        Returns:
            A running context ready to register workspaces.

        Raises:
            NotImplementedError: If ``execution.exchange_url`` is configured.

        """
        from .config import ResourceConfig  # noqa: PLC0415

        execution = config.execution
        resources = execution.resources or {"local": ResourceConfig()}
        default_resource = execution.default_resource or next(iter(resources))
        workspace_roots = {
            name: (spec.workspace_root or run_dir / "workspaces")
            for name, spec in resources.items()
        }
        backends: dict[str, ExecutionBackend] = {}
        manager: object | None = None
        if execution.mode == "local":
            backends = {
                name: LocalExecutionBackend(workspace_roots[name], name) for name in resources
            }
        else:
            if execution.exchange_url is not None:
                raise NotImplementedError(
                    "remote exchange execution is not wired yet; "
                    "omit execution.exchange_url to use the local exchange"
                )
            from academy.exchange import LocalExchangeFactory  # noqa: PLC0415
            from academy.handle import Handle  # noqa: PLC0415
            from academy.manager import Manager  # noqa: PLC0415

            from .remote.agent import ExecutionAgent  # noqa: PLC0415

            manager = await Manager.from_exchange_factory(
                factory=LocalExchangeFactory(),
                executors={name: ThreadPoolExecutor(max_workers=4) for name in resources},
            )
            for name in resources:
                launched = await manager.launch(
                    ExecutionAgent,
                    args=(str(workspace_roots[name]), name),
                    executor=name,
                )
                # Bind the exchange client explicitly: backend calls happen in
                # HTTP-handler tasks that never enter the manager context.
                handle: Handle[ExecutionAgent] = Handle(
                    launched.agent_id, exchange=manager.exchange_client
                )
                backends[name] = AcademyExecutionBackend(handle)
        context = cls(
            backends=backends,
            default_resource=default_resource,
            workspace_roots=workspace_roots,
            mcp_timeout_s=execution.mcp_timeout_s,
            hermes_home=hermes_home,
        )
        context._manager = manager
        try:
            await context.runner.start()
        except BaseException:
            await context.close()
            raise
        return context

    def workspace_dir(self, workspace: str, resource: str | None = None) -> Path:
        """Locate one workspace on the harness-visible filesystem.

        Valid while execution runs on this machine (local mode or the local
        exchange); once resources move behind remote endpoints, workspace
        files must be fetched through the backend instead.

        Args:
            workspace: Workspace identifier.
            resource: Resource whose root to use; default resource if omitted.

        Returns:
            The local workspace directory.

        """
        root = self.workspace_roots[resource or self.default_resource]
        return root / workspace

    def register_workspace(self, workspace: str) -> str:
        """Expose one workspace to Hermes as a header-pinned MCP toolset.

        Args:
            workspace: Workspace identifier to pin.

        Returns:
            The Hermes toolset name for the workspace.

        """
        from .hermes_config import register_workspace_servers, server_name  # noqa: PLC0415

        name = server_name(workspace)
        if name not in self.registered_servers:
            register_workspace_servers(
                self.runner.url,
                [workspace],
                home=self.hermes_home,
                timeout_s=self.mcp_timeout_s,
            )
            self.registered_servers.append(name)
        return name

    async def handshakes(self) -> dict[str, HandshakeReport]:
        """Measure (or reuse) the handshake of every resource.

        Returns:
            Handshake reports keyed by resource name.

        """
        return {name: await self.mcp.handshake(name) for name in sorted(self.backends)}

    async def close(self) -> None:
        """Remove Hermes entries and stop the MCP server and agents."""
        from .hermes_config import unregister_workspace_servers  # noqa: PLC0415

        if self.registered_servers:
            unregister_workspace_servers(self.registered_servers, home=self.hermes_home)
            self.registered_servers = []
        await self.runner.stop()
        manager = self._manager
        self._manager = None
        if manager is not None:
            from academy.handle import exchange_context  # noqa: PLC0415
            from academy.manager import Manager  # noqa: PLC0415

            assert isinstance(manager, Manager)
            # Manager.close() shuts agents down through handles that resolve
            # their exchange client from the context variable normally set by
            # ``async with manager``; set it here since the manager lives
            # outside a single task's context.
            token = exchange_context.set(manager.exchange_client)
            try:
                await manager.close()
            finally:
                exchange_context.reset(token)

    async def __aenter__(self) -> ExecutionContext:
        """Enter the asynchronous context.

        Returns:
            The running context.

        """
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close the context when leaving the asynchronous scope."""
        await self.close()
