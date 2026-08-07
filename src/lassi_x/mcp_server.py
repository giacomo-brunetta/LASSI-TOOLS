"""Local MCP server bridging Hermes tool calls onto execution backends.

The server runs on localhost next to the harness and the Hermes sessions. Each
Hermes role connects with a pinned ``X-Lassi-Workspace`` header, so the model
chooses *which resource* to use (``resource`` argument, discovered via
``list_resources``) but never which workspace: workspace identity always comes
from the connection header written into the Hermes configuration by the
harness.

Tool calls translate one-to-one into :mod:`lassi_x.protocol` messages against
an :class:`~lassi_x.execution.ExecutionBackend`, so the same server serves
in-process local execution and Academy-remote execution without change.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import time
from typing import TYPE_CHECKING, Any

import uvicorn
from mcp.server.fastmcp import Context, FastMCP  # noqa: TC002

from .protocol import ExecRequest, FileGet, FilePut, ListDir

if TYPE_CHECKING:
    import socket
    from collections.abc import Awaitable, Callable, Mapping

    from .execution import ExecutionBackend
    from .protocol import HandshakeReport

logger = logging.getLogger(__name__)

WORKSPACE_HEADER = "x-lassi-workspace"

# Arguments worth putting in a one-line log entry, in the order they read best.
# Everything else (file content, stdin) is summarised by size instead.
_LOGGED_ARGS = ("resource", "path", "cwd", "timeout_s")


def _summarize_call(kwargs: Mapping[str, Any]) -> str:
    """Render tool arguments as compact ``key=value`` text for one log line.

    Args:
        kwargs: Keyword arguments the model supplied for this call.

    Returns:
        Space-separated fields, omitting anything the model left unset.

    """
    fields = []
    command = kwargs.get("command")
    if isinstance(command, list):
        argv = " ".join(str(part) for part in command)
        fields.append(f"argv={argv[:160]!r}" + ("..." if len(argv) > 160 else ""))
    for key in _LOGGED_ARGS:
        value = kwargs.get(key)
        if value is not None:
            fields.append(f"{key}={value}")
    for key in ("content", "stdin"):
        value = kwargs.get(key)
        if isinstance(value, str):
            fields.append(f"{key}_chars={len(value)}")
    return " ".join(fields)


def _logged_tool(name: str) -> Callable[..., Any]:
    """Wrap a tool coroutine so every model call announces itself.

    The execution layer already logged the remote calls tools make, which meant
    a log showed 118 ``put_file`` calls and no hint of which agent asked for
    them or why. This closes that gap at the point the model is actually
    steering.

    Args:
        name: Tool name as the model sees it.

    Returns:
        Decorator preserving the wrapped signature, which FastMCP introspects
        to build the tool schema.

    """

    def decorate(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.monotonic()
            logger.info("tool call %s %s", name, _summarize_call(kwargs))
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                logger.warning(
                    "tool call %s failed in %.1fs %s: %s",
                    name,
                    time.monotonic() - started,
                    type(exc).__name__,
                    exc,
                )
                raise
            logger.info(
                "tool call %s ok in %.1fs reply_chars=%d",
                name,
                time.monotonic() - started,
                len(result) if isinstance(result, str) else 0,
            )
            return result

        return wrapper

    return decorate


_INSTRUCTIONS = """LASSI-X remote execution tools.

Your workspace is fixed by the harness; every path is relative to it. Call
list_resources first to see the available machines (accelerators, toolchains),
then pass the chosen resource name to the other tools. Omitting resource uses
the default machine."""


class LassiMCPServer:
    """MCP tool surface over a registry of named execution backends."""

    def __init__(
        self,
        backends: Mapping[str, ExecutionBackend],
        *,
        default_resource: str,
    ) -> None:
        """Configure the tool surface.

        Args:
            backends: Execution backends keyed by resource name.
            default_resource: Resource used when a tool call names none.

        Raises:
            ValueError: If ``default_resource`` is not a key of ``backends``.

        """
        if default_resource not in backends:
            raise ValueError(f"unknown default resource {default_resource!r}")
        self.backends = dict(backends)
        self.default_resource = default_resource
        self._handshakes: dict[str, HandshakeReport] = {}
        self.server = FastMCP(name="lassi-x", instructions=_INSTRUCTIONS)
        self._register_tools()

    def _backend(self, resource: str | None) -> ExecutionBackend:
        """Resolve one backend by resource name.

        Args:
            resource: Requested resource name, or ``None`` for the default.

        Returns:
            The matching execution backend.

        Raises:
            ValueError: If the resource is unknown.

        """
        name = resource or self.default_resource
        backend = self.backends.get(name)
        if backend is None:
            known = ", ".join(sorted(self.backends))
            raise ValueError(f"unknown resource {name!r}; available resources: {known}")
        return backend

    @staticmethod
    def _workspace(ctx: Context[Any, Any, Any]) -> str:
        """Read the workspace pinned to this connection.

        Args:
            ctx: Tool call context carrying the HTTP request headers.

        Returns:
            The workspace name from the connection header.

        Raises:
            ValueError: If the header is missing.

        """
        request = ctx.request_context.request
        headers = getattr(request, "headers", {})
        workspace = str(headers.get(WORKSPACE_HEADER, ""))
        if not workspace:
            raise ValueError(
                f"connection is missing the {WORKSPACE_HEADER} header; "
                "tool calls must come through a harness-registered MCP server entry"
            )
        return workspace

    async def handshake(self, resource: str) -> HandshakeReport:
        """Return the cached handshake for one resource, measuring it once.

        Args:
            resource: Resource name present in the backend registry.

        Returns:
            The measured handshake report.

        """
        if resource not in self._handshakes:
            self._handshakes[resource] = await self.backends[resource].handshake()
        return self._handshakes[resource]

    def _register_tools(self) -> None:
        """Attach the model-facing tools to the MCP server."""
        server = self.server

        @server.tool(name="list_resources")
        @_logged_tool("list_resources")
        async def list_resources() -> str:
            """List available machines with their accelerators and toolchains."""
            reports = {}
            for name in sorted(self.backends):
                report = await self.handshake(name)
                reports[name] = report.model_dump(mode="json", exclude={"schema_version"})
            return json.dumps(
                {"default_resource": self.default_resource, "resources": reports},
                indent=2,
            )

        @server.tool(name="run_command")
        @_logged_tool("run_command")
        async def run_command(
            ctx: Context[Any, Any, Any],
            command: list[str],
            cwd: str | None = None,
            stdin: str | None = None,
            timeout_s: float = 600.0,
            env: dict[str, str] | None = None,
            resource: str | None = None,
        ) -> str:
            """Run one argv command in your workspace on the chosen machine.

            Args:
                ctx: Tool call context (workspace pinned by the harness).
                command: Command argv list; no shell interpretation.
                cwd: Workspace-relative working directory.
                stdin: Text fed to standard input.
                timeout_s: Deadline in seconds before the command is killed.
                env: Extra non-secret environment variables.
                resource: Machine to run on; default machine when omitted.

            """
            request = ExecRequest(
                workspace=self._workspace(ctx),
                argv=command,
                cwd=cwd,
                stdin_text=stdin,
                timeout_s=timeout_s,
                env=env or {},
            )
            result = await self._backend(resource).execute(request)
            lines = [f"exit_code: {result.exit_code}"]
            if result.timed_out:
                lines.append(f"timed out after {timeout_s} s")
            if result.stdout:
                suffix = " (truncated)" if result.stdout_truncated else ""
                lines.append(f"stdout{suffix}:\n{result.stdout}")
            if result.stderr:
                suffix = " (truncated)" if result.stderr_truncated else ""
                lines.append(f"stderr{suffix}:\n{result.stderr}")
            return "\n".join(lines)

        @server.tool(name="write_file")
        @_logged_tool("write_file")
        async def write_file(
            ctx: Context[Any, Any, Any],
            path: str,
            content: str,
            executable: bool = False,
            resource: str | None = None,
        ) -> str:
            """Write one text file in your workspace on the chosen machine.

            Args:
                ctx: Tool call context (workspace pinned by the harness).
                path: Workspace-relative destination path.
                content: Full file content; parent directories are created.
                executable: Mark the file executable.
                resource: Machine to write on; default machine when omitted.

            """
            request = FilePut(
                workspace=self._workspace(ctx),
                path=path,
                text=content,
                executable=executable,
            )
            stat = await self._backend(resource).put_file(request)
            return f"wrote {stat.size_bytes} bytes to {stat.path} (sha256 {stat.sha256[:12]})"

        @server.tool(name="read_file")
        @_logged_tool("read_file")
        async def read_file(
            ctx: Context[Any, Any, Any],
            path: str,
            resource: str | None = None,
        ) -> str:
            """Read one file from your workspace on the chosen machine.

            Args:
                ctx: Tool call context (workspace pinned by the harness).
                path: Workspace-relative source path.
                resource: Machine to read from; default machine when omitted.

            """
            request = FileGet(workspace=self._workspace(ctx), path=path)
            content = await self._backend(resource).get_file(request)
            if content.encoding == "base64":
                return (
                    f"binary file ({content.size_bytes} bytes, sha256 {content.sha256[:12]}); "
                    "base64 content:\n" + content.content
                )
            note = " (truncated)" if content.truncated else ""
            return f"{content.path}{note}:\n{content.content}"

        @server.tool(name="list_files")
        @_logged_tool("list_files")
        async def list_files(
            ctx: Context[Any, Any, Any],
            path: str = ".",
            resource: str | None = None,
        ) -> str:
            """List one directory of your workspace on the chosen machine.

            Args:
                ctx: Tool call context (workspace pinned by the harness).
                path: Workspace-relative directory.
                resource: Machine to list on; default machine when omitted.

            """
            request = ListDir(workspace=self._workspace(ctx), path=path)
            listing = await self._backend(resource).list_dir(request)
            if not listing.entries:
                return f"{listing.path}: empty"
            lines = []
            for entry in listing.entries:
                size = f" {entry.size_bytes}" if entry.size_bytes is not None else ""
                lines.append(f"{entry.kind}{size} {entry.name}")
            return "\n".join(lines)


class MCPServerRunner:
    """Serve one :class:`LassiMCPServer` over localhost streamable HTTP."""

    def __init__(self, server: LassiMCPServer, *, host: str = "127.0.0.1", port: int = 0) -> None:
        """Configure the runner.

        Args:
            server: Tool surface to serve.
            host: Interface to bind; keep loopback so only local Hermes
                sessions can reach the execution backends.
            port: TCP port; ``0`` binds an ephemeral free port.

        """
        self.server = server
        self.host = host
        self.port = port
        self._uvicorn: uvicorn.Server | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def url(self) -> str:
        """The MCP endpoint URL of the running server.

        Raises:
            RuntimeError: If the server has not been started.

        """
        if self._uvicorn is None or not self._uvicorn.started:
            raise RuntimeError("MCP server is not running")
        server_socket: socket.socket = self._uvicorn.servers[0].sockets[0]
        host, port = server_socket.getsockname()[:2]
        return f"http://{host}:{port}/mcp"

    async def start(self) -> str:
        """Start serving and wait until the port is bound.

        Returns:
            The MCP endpoint URL.

        Raises:
            RuntimeError: If the HTTP server exits during startup.

        """
        app = self.server.server.streamable_http_app()
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="warning")
        self._uvicorn = uvicorn.Server(config)
        self._task = asyncio.create_task(self._uvicorn.serve())
        while not self._uvicorn.started:
            if self._task.done():
                self._task.result()
                raise RuntimeError("MCP server exited during startup")
            await asyncio.sleep(0.02)
        return self.url

    async def stop(self) -> None:
        """Shut the HTTP server down and wait for the serve task to finish."""
        if self._uvicorn is None or self._task is None:
            return
        self._uvicorn.should_exit = True
        await self._task
        self._uvicorn = None
        self._task = None

    async def __aenter__(self) -> MCPServerRunner:
        """Start the server when entering the asynchronous context.

        Returns:
            The running server.

        """
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Stop the server when leaving the asynchronous context."""
        await self.stop()


__all__ = [
    "WORKSPACE_HEADER",
    "LassiMCPServer",
    "MCPServerRunner",
]
