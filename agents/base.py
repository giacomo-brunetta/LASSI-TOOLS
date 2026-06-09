"""Agent ABC and the cross-agent permission router.

SDK communication and logging live in `agents.utils`; per-agent classes live
in their own modules (`agents.analyst`, `agents.planner`, ...). Anything that
multiple agent classes need to share goes here (or in `utils`).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
)

from .utils import claude_send

logger = logging.getLogger(__name__)

PATH_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"}


def render_paths(items: Mapping[str, Path | str]) -> str:
    """Render a key→value mapping as `key: value` lines, one per entry.

    Used by individual agents to format the path/parameter section of their
    task prompts (`input file: ...`, `output file: ...`, etc.) consistently.
    """
    return "\n".join(f"{key}: {value}" for key, value in items.items())


class Agent(ABC):
    """Abstract Claude Agent SDK subagent.

    Subclasses set class-level metadata (`name`, `description`,
    `system_prompt`, `tools`, `model`, `allowed_skills`) and implement
    `build_task_prompt` to render the Task-tool body for their use case.
    `allowed_skills` is auto-injected into both the agent's tool list (adds
    the `Skill` tool when non-empty) and the rendered system prompt, and is
    enforced session-wide by `build_permission_router`.
    """

    name: str = ""
    description: str = ""
    system_prompt: str = ""
    tools: list[str] = []
    model: str = "inherit"
    allowed_skills: list[str] = []

    @abstractmethod
    def build_task_prompt(self, **context: Any) -> str:
        """Render the agent-specific task body. Keyword args are agent-defined."""

    def _rendered_prompt(self) -> str:
        if not self.allowed_skills:
            return self.system_prompt + "\n\nDo not invoke any Skill."
        bullets = "\n- ".join(self.allowed_skills)
        return (
            self.system_prompt
            + "\n\nYou may invoke ONLY these skills via the Skill tool (any "
            "other skill name will be denied):\n- "
            + bullets
        )

    def _rendered_tools(self) -> list[str]:
        tools = list(self.tools)
        if self.allowed_skills and "Skill" not in tools:
            tools.append("Skill")
        return tools

    def definition(self) -> AgentDefinition:
        return AgentDefinition(
            description=self.description,
            prompt=self._rendered_prompt(),
            tools=self._rendered_tools(),
            model=self.model,
        )

    def registration(self) -> tuple[str, AgentDefinition]:
        return self.name, self.definition()

    async def dispatch_agent(self, client: ClaudeSDKClient, **context: Any) -> str:
        body = self.build_task_prompt(**context)
        prompt = "\n".join(
            [
                f"Use the Task tool with subagent_type='{self.name}' to perform the task below.",
                "After the subagent finishes, relay its summary as your final response.",
                "",
                body,
            ]
        )
        logger.info("dispatching agent '%s'", self.name)
        return await claude_send(client, prompt)


def build_permission_router(
    *,
    allowed_paths: list[Path] | None,
    agents: dict[str, Agent],
):
    """Return a `can_use_tool` callback enforcing path scope + per-agent skills.

    `allowed_paths`: absolute path prefixes that bound every Read/Write/Edit
    tool call (`None` disables the path check). Applies session-wide.
    `agents`: keyed by agent name. Each agent's `allowed_skills` bounds which
    skills it may invoke. The main session may call any skill in the union of
    all agent allowlists. Every denial logs a WARNING.
    """

    union_skills: set[str] = set()
    for a in agents.values():
        union_skills.update(a.allowed_skills)

    def _path_in_scope(file_path: str) -> bool:
        if allowed_paths is None:
            return True
        try:
            target = Path(file_path).resolve()
        except (OSError, RuntimeError):
            return False
        return any(target == p or p in target.parents for p in allowed_paths)

    async def router(tool_name: str, tool_input: dict, context: Any):
        raw = tool_input if isinstance(tool_input, dict) else {}

        if tool_name in PATH_TOOLS:
            path = raw.get("file_path") or raw.get("notebook_path") or ""
            if path and not _path_in_scope(str(path)):
                msg = f"path {path!r} is outside the configured scope"
                logger.warning("permission deny: %s", msg)
                return PermissionResultDeny(message=msg)

        if tool_name == "Skill":
            requested = raw.get("skill") or raw.get("name") or ""
            agent_name = (
                getattr(context, "agent_name", None)
                or getattr(context, "subagent_type", None)
            )
            agent = agents.get(agent_name) if agent_name else None
            if agent is not None:
                if requested not in agent.allowed_skills:
                    msg = (
                        f"agent {agent.name!r} may not call skill {requested!r} "
                        f"(allowed: {agent.allowed_skills})"
                    )
                    logger.warning("permission deny: %s", msg)
                    return PermissionResultDeny(message=msg)
            else:
                if requested not in union_skills:
                    msg = (
                        f"main session may not call skill {requested!r} "
                        "(not allowlisted by any agent)"
                    )
                    logger.warning("permission deny: %s", msg)
                    return PermissionResultDeny(message=msg)

        return PermissionResultAllow()

    return router
