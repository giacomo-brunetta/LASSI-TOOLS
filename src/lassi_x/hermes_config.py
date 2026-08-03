"""Register LASSI-X MCP servers in the Hermes client configuration.

Hermes reads ``mcp_servers`` from ``<hermes home>/config.yaml`` and exposes
each server as a toolset named after the server. The harness registers one
entry per agent role, all pointing at the same local LASSI-X MCP server but
pinning a different workspace through the connection header, so a session that
enables toolset ``lassi-x-c1`` can only ever touch workspace ``c1``.

Entries are namespaced with the ``lassi-x-`` prefix and removed at the end of
the run; nothing else in the user's configuration is touched. Concurrent runs
sharing one Hermes home would race on these entries — use per-run
``HERMES_HOME`` values to isolate them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from .artifacts import atomic_write
from .mcp_server import WORKSPACE_HEADER
from .skills import hermes_home

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

SERVER_PREFIX = "lassi-x-"


def server_name(workspace: str) -> str:
    """Return the Hermes MCP server (and toolset) name for one workspace.

    Args:
        workspace: Workspace identifier pinned to the role.

    Returns:
        The namespaced server name.

    """
    return f"{SERVER_PREFIX}{workspace}"


def _config_path(home: Path | None) -> Path:
    """Locate the Hermes client configuration file.

    Args:
        home: Explicit Hermes home, or ``None`` to resolve the default.

    Returns:
        Path to ``config.yaml`` inside the Hermes home.

    """
    return hermes_home(home) / "config.yaml"


def _load(path: Path) -> dict[str, Any]:
    """Load the Hermes configuration, tolerating a missing file.

    Args:
        path: Configuration file path.

    Returns:
        The parsed mapping, or an empty mapping.

    Raises:
        TypeError: If the existing configuration is not a mapping.

    """
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Hermes configuration {path} is not a mapping")
    return data


def register_workspace_servers(
    url: str,
    workspaces: Iterable[str],
    *,
    home: Path | None = None,
    timeout_s: float = 900.0,
) -> list[str]:
    """Register one header-pinned MCP server entry per workspace.

    Args:
        url: Streamable-HTTP endpoint of the running LASSI-X MCP server.
        workspaces: Workspace identifiers needing a Hermes toolset.
        home: Hermes home override; defaults to ``HERMES_HOME`` or ``~/.hermes``.
        timeout_s: Per-tool-call timeout written into each entry; must cover
            the longest remote command a session may run.

    Returns:
        The registered server names, usable directly as Hermes toolsets.

    """
    path = _config_path(home)
    data = _load(path)
    servers = data.setdefault("mcp_servers", {})
    names = []
    for workspace in workspaces:
        name = server_name(workspace)
        servers[name] = {
            "url": url,
            "headers": {WORKSPACE_HEADER: workspace},
            "timeout": int(timeout_s),
            # LASSI-X exposes execution through MCP tools, not MCP resources or
            # prompts. Disabling Hermes' generic utilities avoids collisions
            # with our ``list_resources`` tool and its local skill machinery.
            "tools": {"resources": False, "prompts": False},
        }
        names.append(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, yaml.safe_dump(data, sort_keys=True))
    return names


def unregister_workspace_servers(
    names: Iterable[str],
    *,
    home: Path | None = None,
) -> list[str]:
    """Remove previously registered LASSI-X MCP server entries.

    Only entries carrying the LASSI-X prefix are eligible; other names are
    ignored so a caller bug cannot delete a user's own server configuration.

    Args:
        names: Server names returned by :func:`register_workspace_servers`.
        home: Hermes home override; defaults to ``HERMES_HOME`` or ``~/.hermes``.

    Returns:
        The names actually removed.

    """
    path = _config_path(home)
    data = _load(path)
    servers = data.get("mcp_servers")
    if not isinstance(servers, dict):
        return []
    removed = []
    for name in names:
        if name.startswith(SERVER_PREFIX) and name in servers:
            del servers[name]
            removed.append(name)
    if not servers:
        data.pop("mcp_servers", None)
    atomic_write(path, yaml.safe_dump(data, sort_keys=True))
    return removed


def registered_lassi_servers(home: Path | None = None) -> Mapping[str, Any]:
    """Return the LASSI-X MCP server entries currently registered.

    Args:
        home: Hermes home override; defaults to ``HERMES_HOME`` or ``~/.hermes``.

    Returns:
        Mapping of server name to entry for every LASSI-X-prefixed server.

    """
    servers = _load(_config_path(home)).get("mcp_servers")
    if not isinstance(servers, dict):
        return {}
    return {name: entry for name, entry in servers.items() if name.startswith(SERVER_PREFIX)}
