"""SDK communication + logging helpers shared by every agent."""

from __future__ import annotations

import logging

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

logger = logging.getLogger(__name__)


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
        tools = data.get("tools") or data.get("available_tools") or []
        agents = data.get("agents") or []
        skills = data.get("skills") or []
        logger.info(
            "claude session init: model=%s tools=%d agents=%d skills=%d",
            data.get("model"), len(tools), len(agents), len(skills),
        )
        logger.debug(
            "claude session init full lists: tools=%s agents=%s skills=%s",
            tools, agents, skills,
        )
    elif subtype in {"skill", "skill_loaded", "skill_activated"}:
        logger.info("claude loaded skill: %s", data.get("name") or data)
    elif subtype in {"agent", "subagent_started"}:
        logger.info("claude started subagent: %s", data.get("name") or data)
    else:
        logger.debug("claude system event %s: %s", subtype, data)


async def claude_send(client: ClaudeSDKClient, prompt: str) -> str:
    """Send `prompt` on a connected ClaudeSDKClient; return the final text."""
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
