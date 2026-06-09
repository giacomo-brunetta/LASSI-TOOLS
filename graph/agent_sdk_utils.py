from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

def _log_system_message(message: SystemMessage) -> None:
    subtype = getattr(message, "subtype", None) or "system"
    data = getattr(message, "data", {}) or {}
    if subtype == "init":
        logger.info(
            "claude session init: model=%s tools=%s agents=%s",
            data.get("model"),
            data.get("tools") or data.get("available_tools"),
            data.get("agents"),
        )
    else:
        logger.debug("claude system event %s: %s", subtype, data)


async def claude_send(client: ClaudeSDKClient, prompt: str) -> str:
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


async def _ensure_claude_client(state: PipelineStage) -> ClaudeSDKClient:
    if state.claude_client is not None:
        return state.claude_client
    options = ClaudeAgentOptions(
        cwd=str(state.repo_path),
        model=CLAUDE_MODEL,
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task"],
        agents={CONFIG_BUILDER_AGENT: CONFIG_BUILDER},
    )
    client = ClaudeSDKClient(options=options)
    await client.connect()
    state.claude_client = client
    return client