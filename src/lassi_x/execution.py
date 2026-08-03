"""Execution backends: one interface for local and Academy-remote work.

The harness and the MCP tool server both talk to an :class:`ExecutionBackend`.
:class:`LocalExecutionBackend` runs everything in-process against a local
directory, while :class:`AcademyExecutionBackend` forwards each call to an
:class:`~lassi_x.remote.agent.ExecutionAgent` handle living on an HPC
resource. Both share the operation semantics in :mod:`lassi_x.remote.ops`, so
switching a run between local and remote execution changes transport only.
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from .protocol import MAX_INLINE_BYTES, FileGet, FilePut
from .remote import ops

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from academy.handle import Handle

    from .config import ResourceConfig, RunConfig
    from .protocol import (
        DirListing,
        ExecRequest,
        ExecResult,
        FileContent,
        FileStat,
        HandshakeReport,
        ListDir,
    )
    from .remote.agent import ExecutionAgent


class ExecutionBackend(ABC):
    """Workspace-confined execution and file operations on one resource."""

    _cached_handshake: HandshakeReport | None = None

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

    async def cached_handshake(self) -> HandshakeReport:
        """Return the handshake, measuring it at most once per backend.

        Returns:
            The measured or previously cached handshake report.

        """
        if self._cached_handshake is None:
            self._cached_handshake = await self.handshake()
        return self._cached_handshake


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


def _resource_executor(name: str, spec: ResourceConfig) -> Executor:
    """Build the executor that launches one resource's execution agent.

    Args:
        name: Resource name, used in error messages.
        spec: Resource configuration.

    Returns:
        A Globus Compute executor for endpoint resources, otherwise a local
        thread pool.

    Raises:
        RuntimeError: If an endpoint is configured but ``globus-compute-sdk``
            is not installed.

    """
    if spec.endpoint_id is None:
        return ThreadPoolExecutor(max_workers=4)
    try:
        from globus_compute_sdk import Executor as GlobusComputeExecutor  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            f"resource {name!r} names Globus Compute endpoint {spec.endpoint_id} "
            "but globus-compute-sdk is not installed; install lassi-x[globus]"
        ) from exc
    return GlobusComputeExecutor(spec.endpoint_id)  # type: ignore[no-any-return]


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
        mirror_root: Path,
        mcp_timeout_s: float,
        hermes_home: Path | None = None,
    ) -> None:
        """Wire the context; use :meth:`start` instead of calling this directly.

        Args:
            backends: Execution backends keyed by resource name.
            default_resource: Resource used when a request names none.
            mirror_root: Harness-local directory holding the mirrored copy of
                every workspace's artifacts of record.
            mcp_timeout_s: Per-tool-call timeout written into Hermes entries.
            hermes_home: Hermes home override for configuration registration.

        """
        from .mcp_server import LassiMCPServer, MCPServerRunner  # noqa: PLC0415

        self.backends = backends
        self.default_resource = default_resource
        self.mirror_root = mirror_root
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
        agents run through a local exchange on this machine; with one, the
        manager connects to the remote (Globus-authenticated) exchange and
        resources carrying an ``endpoint_id`` are launched onto their Globus
        Compute endpoints.

        Args:
            config: Validated run configuration.
            run_dir: Root artifact directory for the current pipeline run.
            hermes_home: Hermes home override for configuration registration.

        Returns:
            A running context ready to register workspaces.

        Raises:
            RuntimeError: If an endpoint resource is configured but the
                ``globus-compute-sdk`` optional dependency is not installed.

        """
        from .config import ResourceConfig  # noqa: PLC0415

        execution = config.execution
        resources = execution.resources or {"local": ResourceConfig()}
        default_resource = execution.default_resource or next(iter(resources))
        mirror_root = run_dir / "workspaces"
        backends: dict[str, ExecutionBackend] = {}
        manager: object | None = None
        if execution.mode == "local":
            backends = {
                name: LocalExecutionBackend(spec.workspace_root or mirror_root, name)
                for name, spec in resources.items()
            }
        else:
            from academy.exchange import LocalExchangeFactory  # noqa: PLC0415
            from academy.handle import Handle  # noqa: PLC0415
            from academy.manager import Manager  # noqa: PLC0415

            from .remote.agent import ExecutionAgent  # noqa: PLC0415

            executors: dict[str, Executor | None] = {
                name: _resource_executor(name, spec) for name, spec in resources.items()
            }
            if execution.exchange_url is None:
                manager = await Manager.from_exchange_factory(
                    factory=LocalExchangeFactory(), executors=executors
                )
            else:
                from academy.exchange.cloud.client import HttpExchangeFactory  # noqa: PLC0415

                manager = await Manager.from_exchange_factory(
                    factory=HttpExchangeFactory(
                        execution.exchange_url,
                        auth_method="globus" if execution.auth == "globus" else None,
                    ),
                    executors=executors,
                )
            for name, spec in resources.items():
                agent_root = spec.workspace_root or mirror_root
                launched = await manager.launch(
                    ExecutionAgent,
                    args=(str(agent_root), name),
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
            mirror_root=mirror_root,
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

    def workspace_dir(self, workspace: str) -> Path:
        """Locate the harness-local mirror directory of one workspace.

        In local execution this is the workspace itself; for remote resources
        it holds the mirrored artifacts of record fetched via
        :meth:`mirror_file`.

        Args:
            workspace: Workspace identifier.

        Returns:
            The local mirror directory.

        """
        return self.mirror_root / workspace

    def backend(self, resource: str | None = None) -> ExecutionBackend:
        """Resolve one execution backend.

        Args:
            resource: Resource name; default resource if omitted.

        Returns:
            The matching backend.

        """
        return self.backends[resource or self.default_resource]

    async def stage_bytes(self, workspace: str, path: str, data: bytes) -> None:
        """Write one file into a workspace on every resource.

        Staging fans out to all resources so an agent may run commands against
        the staged inputs on whichever machine it selects.

        Args:
            workspace: Workspace identifier.
            path: Workspace-relative destination path.
            data: File content.

        Raises:
            ValueError: If the payload exceeds the inline message limit.

        """
        encoded = base64.b64encode(data).decode()
        if len(encoded) > 2 * MAX_INLINE_BYTES:
            raise ValueError(
                f"staged file {path!r} exceeds the inline transfer limit "
                f"({len(data)} bytes); large fixtures need a transfer mechanism"
            )
        request = FilePut(workspace=workspace, path=path, content_b64=encoded)
        for backend in self.backends.values():
            await backend.put_file(request)

    async def fetch_bytes(self, workspace: str, path: str, resource: str | None = None) -> bytes:
        """Fetch one workspace file from a resource, chunking large files.

        Args:
            workspace: Workspace identifier.
            path: Workspace-relative file path.
            resource: Resource to fetch from; default resource if omitted.

        Returns:
            The complete file content.

        """
        return await fetch_bytes(self.backend(resource), workspace, path)

    async def mirror_file(self, workspace: str, path: str, resource: str | None = None) -> Path:
        """Copy one workspace file into the harness-local mirror directory.

        Args:
            workspace: Workspace identifier.
            path: Workspace-relative file path.
            resource: Resource to fetch from; default resource if omitted.

        Returns:
            The local mirrored file path.

        """
        data = await self.fetch_bytes(workspace, path, resource)
        destination = self.workspace_dir(workspace) / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return destination

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
