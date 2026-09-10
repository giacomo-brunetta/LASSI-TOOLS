"""Lifecycle and resource routing for one pipeline run."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from .academy import (
    SHUTDOWN_TIMEOUT_S,
    AcademyExecutionBackend,
    ResourceUnavailableError,
    _add_academy_send_retry,
    _disable_academy_stream_deadline,
    _resource_executor,
)
from .local import LocalExecutionBackend
from .transfer import fetch_bytes, put_bytes

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from academy.handle import Handle

    from ..config import RunConfig
    from ..protocol import HandshakeReport
    from ..remote.agent import ExecutionAgent
    from .base import ExecutionBackend

logger = logging.getLogger("lassi_x.execution")

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
        enable_memory: bool = False,
        dead_resources: dict[str, str] | None = None,
    ) -> None:
        """Wire the context; use :meth:`start` instead of calling this directly.

        Args:
            backends: Execution backends keyed by resource name.
            default_resource: Resource used when a request names none.
            mirror_root: Harness-local directory holding the mirrored copy of
                every workspace's artifacts of record.
            mcp_timeout_s: Per-tool-call timeout written into Hermes entries.
            hermes_home: Hermes home override for configuration registration.
            enable_memory: Whether to activate the Mem0 memory provider in the
                Hermes configuration for the duration of the run.
            dead_resources: Live mapping of retired resource to the reason it
                was retired, shared with the backends that populate it.

        """
        from ..mcp_server import LassiMCPServer, MCPServerRunner  # noqa: PLC0415

        self.backends = backends
        self.dead_resources = {} if dead_resources is None else dead_resources
        self.default_resource = default_resource
        self.mirror_root = mirror_root
        self.mcp_timeout_s = mcp_timeout_s
        self.hermes_home = hermes_home
        self.enable_memory = enable_memory
        self.mcp = LassiMCPServer(backends, default_resource=default_resource)
        self.runner = MCPServerRunner(self.mcp)
        self.registered_servers: list[str] = []
        self._manager: object | None = None
        self._memory_active = False
        self._memory_previous: str | None = None

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
        from ..config import ResourceConfig  # noqa: PLC0415

        execution = config.execution
        resources = execution.resources or {"local": ResourceConfig()}
        default_resource = execution.default_resource or next(iter(resources))
        mirror_root = run_dir / "workspaces"
        backends: dict[str, ExecutionBackend] = {}
        dead_resources: dict[str, str] = {}
        manager: object | None = None

        def record_dead(resource: str, detail: str) -> None:
            """Keep the first retirement reason for a resource."""
            dead_resources.setdefault(resource, detail)

        if execution.mode == "local":
            backends = {
                name: LocalExecutionBackend(spec.workspace_root or mirror_root, name)
                for name, spec in resources.items()
            }
        else:
            from academy.exchange import LocalExchangeFactory  # noqa: PLC0415
            from academy.handle import Handle  # noqa: PLC0415
            from academy.manager import Manager  # noqa: PLC0415

            from ..remote.agent import ExecutionAgent  # noqa: PLC0415

            executors: dict[str, Executor | None] = {
                name: _resource_executor(name, spec) for name, spec in resources.items()
            }
            if execution.exchange_url is None:
                manager = await Manager.from_exchange_factory(
                    factory=LocalExchangeFactory(), executors=executors
                )
            else:
                from academy.exchange.cloud.client import HttpExchangeFactory  # noqa: PLC0415

                class PersistentHttpExchangeFactory(HttpExchangeFactory):
                    """Create hosted-exchange transports safe for long pipelines."""

                    async def _create_transport(self, *args: Any, **kwargs: Any) -> Any:
                        transport = await super()._create_transport(*args, **kwargs)
                        _disable_academy_stream_deadline(transport)
                        _add_academy_send_retry(transport)
                        return transport

                manager = await Manager.from_exchange_factory(
                    factory=PersistentHttpExchangeFactory(
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
                backends[name] = AcademyExecutionBackend(
                    handle,
                    name,
                    call_timeout_s=execution.call_timeout_s,
                    dead_after_timeouts=execution.dead_after_timeouts,
                    on_dead=record_dead,
                    heartbeat_interval_s=execution.heartbeat_interval_s,
                    heartbeat_misses=execution.heartbeat_misses,
                    pause_max_s=execution.pause_max_s,
                )
        context = cls(
            backends=backends,
            default_resource=default_resource,
            mirror_root=mirror_root,
            mcp_timeout_s=execution.mcp_timeout_s,
            hermes_home=hermes_home,
            enable_memory=config.memory.enabled,
            dead_resources=dead_resources,
        )
        context._manager = manager
        try:
            for backend in backends.values():
                await backend.start_keepalive()
            await context.runner.start()
            if context.enable_memory:
                from ..hermes_config import enable_memory_provider  # noqa: PLC0415

                context._memory_previous = enable_memory_provider(home=context.hermes_home)
                context._memory_active = True
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

    def require_live_resources(self) -> None:
        """Fail the run if any resource has been taken out of service.

        Called between agent turns rather than inside them. A retired resource
        cannot produce a measurement, so every turn taken after one dies buys
        nothing at full price -- and the results it does produce have a hole in
        them exactly where the retired resource's numbers belong, which is
        worse than no results at all.

        Raises:
            ResourceUnavailableError: If at least one resource is retired.

        """
        if not self.dead_resources:
            return
        resource, detail = next(iter(sorted(self.dead_resources.items())))
        raise ResourceUnavailableError(resource, detail)

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

        """
        for backend in self.backends.values():
            await put_bytes(backend, workspace, path, data)

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
        from ..hermes_config import register_workspace_servers, server_name  # noqa: PLC0415

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
        """Measure (or reuse) the handshake of every resource, concurrently.

        Probing in parallel keeps one mute resource from masking the health of
        the others: sequentially, the first unanswered handshake consumed the
        whole preflight and the report named only that resource.

        Returns:
            Handshake reports keyed by resource name.

        """
        names = sorted(self.backends)
        reports = await asyncio.gather(*(self.mcp.handshake(name) for name in names))
        return dict(zip(names, reports, strict=True))

    async def close(self) -> None:
        """Remove Hermes entries and stop the MCP server and agents.

        Cleanup is best-effort: a failure while shutting remote agents down
        (for example when the exchange is unreachable) is logged and
        suppressed so it never masks the error that ended the run.

        Agent shutdown is bounded for the same reason the calls it mirrors
        are. ``Manager.close`` asks each agent to stop and waits for it to
        acknowledge, so closing against the very resource that just went mute
        hangs exactly where the run did -- and does it in teardown, after the
        result is already known. A preflight that had correctly abandoned two
        unreachable resources still failed to print its verdict because of it.
        """
        from ..hermes_config import (  # noqa: PLC0415
            restore_memory_provider,
            unregister_workspace_servers,
        )

        if self.registered_servers:
            unregister_workspace_servers(self.registered_servers, home=self.hermes_home)
            self.registered_servers = []
        if self._memory_active:
            restore_memory_provider(self._memory_previous, home=self.hermes_home)
            self._memory_active = False
            self._memory_previous = None
        # Before the manager goes, so a probe cannot outlive the exchange it
        # talks through and log a spurious miss during teardown.
        for backend in self.backends.values():
            await backend.stop_keepalive()
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
                await asyncio.wait_for(manager.close(), SHUTDOWN_TIMEOUT_S)
            except TimeoutError:
                logger.warning(
                    "execution manager shutdown abandoned after %.0fs; "
                    "one or more agents did not acknowledge",
                    SHUTDOWN_TIMEOUT_S,
                )
            except Exception as exc:  # noqa: BLE001  # cleanup must not mask run errors
                logger.warning("execution manager shutdown failed: %s: %s", type(exc).__name__, exc)
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
