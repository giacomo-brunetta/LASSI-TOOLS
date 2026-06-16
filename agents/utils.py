"""SDK communication + logging helpers shared by every agent."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeSDKClient, ToolUseBlock, SystemMessage


@dataclass
class AgentTurn:
    """One round-trip on a Claude session: final text + usage snapshot.

    `usage` is normalized from `ResultMessage.usage` (which is an open dict) so
    callers can rely on the keys below being present (zero when the API does
    not report them, e.g. no cache hits).
    """

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    duration_ms: int = 0
    total_cost_usd: float = 0.0

    def merge(self, other: "AgentTurn") -> "AgentTurn":
        """Return a new turn with summed usage (used to aggregate per role)."""
        return AgentTurn(
            text=other.text or self.text,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_input_tokens=self.cache_read_input_tokens + other.cache_read_input_tokens,
            cache_creation_input_tokens=(
                self.cache_creation_input_tokens + other.cache_creation_input_tokens
            ),
            duration_ms=self.duration_ms + other.duration_ms,
            total_cost_usd=self.total_cost_usd + other.total_cost_usd,
        )

    def usage_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "duration_ms": self.duration_ms,
            "total_cost_usd": self.total_cost_usd,
        }
# ///////////////////////////////////////////////////////////////////////////////
#                              LOGGING UTILS
# ///////////////////////////////////////////////////////////////////////////////

logger = logging.getLogger(__name__)


def _log_tool_use(block: "ToolUseBlock") -> None:
    raw = block.input if isinstance(block.input, dict) else {}

    # Log Task
    if block.name == "Task":
        sub = raw.get("subagent_type") or "<unspecified>"
        desc = raw.get("description") or raw.get("prompt", "")
        if isinstance(desc, str) and len(desc) > 120:
            desc = desc[:117] + "..."
        logger.info("claude dispatched agent '%s' (task: %s)", sub, desc)

    # Log Skill Invocation
    elif block.name == "Skill":
        skill = raw.get("skill") or raw.get("name") or "<unknown>"
        args = raw.get("args") or raw.get("arguments") or ""
        logger.info("claude invoked skill '%s' args=%r", skill, args)

    # Log Generic Tool Invocation
    else:
        logger.debug("claude tool use: %s input=%s", block.name, raw)


def _log_system_message(message: "SystemMessage") -> None:
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

# ///////////////////////////////////////////////////////////////////////////////
#                              Agent Invocation Helper
# ///////////////////////////////////////////////////////////////////////////////

async def claude_send(client: "ClaudeSDKClient", prompt: str) -> AgentTurn:
    """Send `prompt` on a connected ClaudeSDKClient; return text + usage.

    The returned `AgentTurn` carries both the final response text and the
    normalized token usage from the SDK's `ResultMessage`. Usage fields are
    zero when the API does not report them (e.g. caches not populated).
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ResultMessage,
        SystemMessage,
        TextBlock,
        ToolUseBlock,
    )

    await client.query(prompt)
    final_text = ""
    turn = AgentTurn(text="")
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
            usage = getattr(message, "usage", None) or {}
            turn.input_tokens = int(usage.get("input_tokens", 0) or 0)
            turn.output_tokens = int(usage.get("output_tokens", 0) or 0)
            turn.cache_read_input_tokens = int(
                usage.get("cache_read_input_tokens", 0) or 0
            )
            turn.cache_creation_input_tokens = int(
                usage.get("cache_creation_input_tokens", 0) or 0
            )
            turn.duration_ms = int(getattr(message, "duration_ms", 0) or 0)
            turn.total_cost_usd = float(getattr(message, "total_cost_usd", 0.0) or 0.0)
            logger.info(
                "claude turn finished: stop_reason=%s duration_ms=%d "
                "tokens_in=%d tokens_out=%d cache_read=%d cost=%.4f",
                getattr(message, "stop_reason", None),
                turn.duration_ms,
                turn.input_tokens,
                turn.output_tokens,
                turn.cache_read_input_tokens,
                turn.total_cost_usd,
            )
    turn.text = final_text
    return turn
