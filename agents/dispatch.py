"""Pluggable dispatch backend for `Agent.dispatch_agent`.

By default an agent runs in-process via the Claude SDK (see `Agent.dispatch_agent`).
The graph orchestrator can register an alternative backend (e.g. one that
runs the agent inside a Docker container) so the in-process Claude session
becomes one option among others, transparently to call sites.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Agent

DispatchBackend = Callable[..., Awaitable[str]]

_backend: DispatchBackend | None = None


def set_dispatch_backend(fn: DispatchBackend | None) -> None:
    global _backend
    _backend = fn


def get_dispatch_backend() -> DispatchBackend | None:
    return _backend
