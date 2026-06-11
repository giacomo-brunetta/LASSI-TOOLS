"""Agent ABC and the cross-agent permission router.

Each agent owns its own short-lived `ClaudeSDKClient` session. Tool and
skill scoping is set declaratively on `ClaudeAgentOptions`; the only thing
the runtime router still enforces is the filesystem path scope, which the
SDK cannot express declaratively.

The static parts of every agent (description, tool list, system prompt)
live in `.claude/agents/<name>.md` — the same files Claude Code itself
reads — so the spec is shared between this Python pipeline and any direct
Claude Code subagent invocation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeSDKClient

# claude_agent_sdk is only required inside the graph container. Import lazily
# so the host side (which only needs to launch the container) doesn't pull
# the SDK in.

logger = logging.getLogger(__name__)

PATH_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"}

_REPO_SPEC_DIR = Path(__file__).resolve().parent.parent / ".claude" / "agents"
_USER_SPEC_DIR = Path.home() / ".claude" / "agents"


def render_paths(items: Mapping[str, Path | str]) -> str:
    """Render a key→value mapping as `key: value` lines, one per entry."""
    return "\n".join(f"{key}: {value}" for key, value in items.items())


@dataclass
class AgentSpec:
    name: str
    description: str
    tools: list[str]
    system_prompt: str
    source: Path


def _parse_spec(path: Path) -> AgentSpec:
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing frontmatter '---' opener")
    # Find the closing fence on its own line.
    body_start = text.find("\n---", 3)
    if body_start == -1:
        raise ValueError(f"{path}: missing frontmatter '---' closer")
    fm_block = text[3:body_start].strip()
    body = text[body_start + 4 :].lstrip("\n").rstrip() + "\n"
    meta: dict[str, str] = {}
    for line in fm_block.splitlines():
        line = line.rstrip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip().strip('"').strip("'")
    tools = [t.strip() for t in meta.get("tools", "").split(",") if t.strip()]
    return AgentSpec(
        name=meta.get("name", path.stem),
        description=meta.get("description", ""),
        tools=tools,
        system_prompt=body,
        source=path,
    )


def load_agent_spec(name: str, *, spec_dir: Path | None = None) -> AgentSpec:
    """Locate and parse `<name>.md` from the standard Claude agents dirs.

    Search order: explicit `spec_dir`, then the repo-local
    `LASSI-TOOLS/.claude/agents/`, then `~/.claude/agents/`. Raises
    `FileNotFoundError` listing every path tried.
    """
    candidates: list[Path] = []
    if spec_dir is not None:
        candidates.append(spec_dir / f"{name}.md")
    candidates.append(_REPO_SPEC_DIR / f"{name}.md")
    candidates.append(_USER_SPEC_DIR / f"{name}.md")
    for path in candidates:
        if path.is_file():
            return _parse_spec(path)
    tried = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(f"agent spec not found for {name!r}; tried: {tried}")


class Agent(ABC):
    """Abstract Claude Agent.

    Subclasses set `name`, `allowed_skills`, `model`, and implement
    `build_task_prompt`. The static spec — `description`, `tools`, and
    `system_prompt` — is loaded at construction time from
    `.claude/agents/<name>.md` (the same file Claude Code itself reads), so
    the prompt has a single source of truth shared between this pipeline
    and any direct Claude Code subagent invocation.

    `dispatch_agent` opens a `ClaudeSDKClient` on the first call and reuses
    it for every subsequent dispatch on the same instance, so the agent
    accumulates conversation memory across plan/code/retry rounds. Call
    `close()` (typically once per pipeline) to disconnect.
    """

    name: str = ""
    model: str = "inherit"
    allowed_skills: list[str] = []
    # "write" agents need a read-write project mount (they edit source files
    # or LASSI artifacts under the project tree). "read" agents only inspect
    # the project and can share a single read-only container with their peers.
    access_mode: str = "write"

    def __init__(self, spec_dir: Path | None = None) -> None:
        if not self.name:
            raise ValueError(f"{type(self).__name__}.name must be set")
        spec = load_agent_spec(self.name, spec_dir=spec_dir)
        self.description = spec.description
        self.tools = spec.tools
        self.system_prompt = spec.system_prompt
        self.spec_source = spec.source
        self._client: "ClaudeSDKClient | None" = None
        self._client_options_key: tuple | None = None

    @abstractmethod
    def build_task_prompt(self, **context: Any) -> str:
        """Render the agent-specific task body. Keyword args are agent-defined."""

    def build_options(
        self,
        *,
        cwd: Path,
        allowed_paths: list[Path] | None = None,
        model: str | None = None,
        permission_mode: str = "acceptEdits",
    ):
        """Build the `ClaudeAgentOptions` that scope this agent's session."""
        from claude_agent_sdk import ClaudeAgentOptions  # lazy: SDK only on the run side

        allowed_tools = list(self.tools)
        if self.allowed_skills and "Skill" not in allowed_tools:
            allowed_tools.append("Skill")
        return ClaudeAgentOptions(
            cwd=str(cwd),
            model=model if model is not None else (None if self.model == "inherit" else self.model),
            permission_mode=permission_mode,
            system_prompt=self.system_prompt,
            allowed_tools=allowed_tools,
            skills=self.allowed_skills or None,
            can_use_tool=build_permission_router(allowed_paths=allowed_paths),
        )

    async def dispatch_agent(
        self,
        *,
        cwd: Path,
        allowed_paths: list[Path] | None = None,
        model: str | None = None,
        permission_mode: str = "acceptEdits",
        **context: Any,
    ) -> str:
        from .utils import claude_send

        key = (
            str(cwd),
            tuple(str(p) for p in (allowed_paths or [])),
            model,
            permission_mode,
        )
        if self._client is None:
            from claude_agent_sdk import ClaudeSDKClient  # lazy: SDK only on the run side
            options = self.build_options(
                cwd=cwd,
                allowed_paths=allowed_paths,
                model=model,
                permission_mode=permission_mode,
            )
            logger.info("opening persistent session for agent '%s'", self.name)
            self._client = ClaudeSDKClient(options=options)
            await self._client.connect()
            self._client_options_key = key
        elif key != self._client_options_key:
            logger.warning(
                "agent '%s' re-dispatched with different session params; "
                "reusing existing session (params ignored)",
                self.name,
            )
        body = self.build_task_prompt(**context)
        logger.info("dispatching agent '%s' (turn on persistent session)", self.name)
        return await claude_send(self._client, body)

    async def close(self) -> None:
        """Disconnect the cached Claude session, if any. Idempotent."""
        if self._client is None:
            return
        logger.info("closing persistent session for agent '%s'", self.name)
        try:
            await self._client.disconnect()
        finally:
            self._client = None
            self._client_options_key = None


def build_permission_router(*, allowed_paths: list[Path] | None):
    """Return a `can_use_tool` callback enforcing path scope.

    `allowed_paths`: absolute path prefixes that bound every Read/Write/Edit
    tool call (`None` disables the check). Tool and skill allowlists are
    enforced by `ClaudeAgentOptions.allowed_tools` / `skills`, so this
    router only handles the path-scope policy the SDK cannot express
    declaratively.
    """

    from claude_agent_sdk import (  # lazy: SDK only on the run side
        PermissionResultAllow,
        PermissionResultDeny,
    )

    def _path_in_scope(file_path: str) -> bool:
        if allowed_paths is None:
            return True
        try:
            target = Path(file_path).resolve()
        except (OSError, RuntimeError):
            return False
        return any(target == p or p in target.parents for p in allowed_paths)

    async def router(tool_name: str, tool_input: dict, _context: Any):
        del _context
        raw = tool_input if isinstance(tool_input, dict) else {}
        if tool_name in PATH_TOOLS:
            path = raw.get("file_path") or raw.get("notebook_path") or ""
            if path and not _path_in_scope(str(path)):
                msg = f"path {path!r} is outside the configured scope"
                logger.warning("permission deny: %s", msg)
                return PermissionResultDeny(message=msg)
        return PermissionResultAllow()

    return router
