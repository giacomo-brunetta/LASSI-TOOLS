from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

logger = logging.getLogger(__name__)

PATH_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"}
PathPermissionFn = Callable[[str, dict, Any], Awaitable[Any]]


def _log_tool_use(block: ToolUseBlock) -> None:
    raw = block.input if isinstance(block.input, dict) else {}
    if block.name == "Task":
        sub = raw.get("subagent_type") or "<unspecified>"
        desc = raw.get("description") or raw.get("prompt", "")
        if isinstance(desc, str) and len(desc) > 120:
            desc = desc[:117] + "..."
        logger.info("claude dispatched agent '%s' (task: %s)", sub, desc)
    elif block.name == "Skill":
        skill = raw.get("skill") or raw.get("name") or "<unknown>"
        args = raw.get("args") or raw.get("arguments") or ""
        logger.info("claude invoked skill '%s' args=%r", skill, args)
    else:
        logger.debug("claude tool use: %s input=%s", block.name, raw)


def _log_system_message(message: SystemMessage) -> None:
    subtype = getattr(message, "subtype", None) or "system"
    data = getattr(message, "data", {}) or {}
    if subtype == "init":
        logger.info(
            "claude session init: model=%s tools=%s agents=%s skills=%s",
            data.get("model"),
            data.get("tools") or data.get("available_tools"),
            data.get("agents"),
            data.get("skills"),
        )
    elif subtype in {"skill", "skill_loaded", "skill_activated"}:
        logger.info("claude loaded skill: %s", data.get("name") or data)
    elif subtype in {"agent", "subagent_started"}:
        logger.info("claude started subagent: %s", data.get("name") or data)
    else:
        logger.debug("claude system event %s: %s", subtype, data)


async def claude_send(client: ClaudeSDKClient, prompt: str) -> str:
    """Send `prompt` on an already-connected ClaudeSDKClient and return the final text."""
    await client.query(prompt)
    final_text = ""
    async for message in client.receive_response():
        if isinstance(message, SystemMessage):
            _log_system_message(message)
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    _log_tool_use(block)
                elif isinstance(block, TextBlock) and block.text:
                    final_text = block.text
        elif isinstance(message, ResultMessage):
            if message.result:
                final_text = message.result
            logger.info(
                "claude turn finished: stop_reason=%s duration_ms=%s cost=%s",
                getattr(message, "stop_reason", None),
                getattr(message, "duration_ms", None),
                getattr(message, "total_cost_usd", None),
            )
    return final_text


class Agent(ABC):
    """Abstract Claude Agent SDK subagent.

    Subclasses set the class-level metadata (`name`, `description`,
    `system_prompt`, `tools`, `model`, `allowed_skills`) and implement
    `build_task_prompt` to render the Task-tool body for their specific use
    case. `allowed_skills` is auto-injected into both the agent's tool list
    (adds the `Skill` tool when non-empty) and the rendered system prompt,
    and is enforced at session level by `build_permission_router`.
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
            + "\n\nYou may invoke ONLY these skills via the Skill tool (any other "
            "skill name will be denied):\n- "
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

    `allowed_paths` is a list of absolute path prefixes that bound every
    Read/Write/Edit-class tool call (applies session-wide). `None` disables
    the path check. `agents` keys by agent name; each agent's `allowed_skills`
    list bounds which skills that subagent may invoke. The main session
    (no subagent) may call any skill in the union of all agent allowlists.
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
