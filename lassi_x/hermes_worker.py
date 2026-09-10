from __future__ import annotations

import contextlib
import json
import os
import shlex
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from lassi_x.protocol import (
    TurnUsage,
    WorkerFailure,
    WorkerInit,
    WorkerReady,
    WorkerResponse,
    WorkerSend,
    WorkerTurn,
    parse_worker_request,
)

PROTOCOL_STREAM = sys.stdout


def scrub_sensitive(text: str, secrets: list[str]) -> str:
    """Remove known credential values from worker diagnostics.

    Args:
        text: Exception or traceback text intended for the JSONL protocol.
        secrets: Credential values resolved in the current worker.

    Returns:
        Diagnostic text with every non-empty secret replaced by a fixed marker.

    """
    scrubbed = text
    for secret in secrets:
        if secret:
            scrubbed = scrubbed.replace(secret, "[REDACTED]")
    return scrubbed


def emit(response: WorkerResponse) -> None:
    """Write one response message to the worker's JSONL protocol stream.

    Args:
        response: Validated protocol response returned to the parent session.

    """
    PROTOCOL_STREAM.write(response.model_dump_json() + "\n")
    PROTOCOL_STREAM.flush()


def resolve_api_key(request: WorkerInit) -> str | None:
    """Resolve an API credential from the configured external source.

    Environment-variable configuration takes precedence. For Argo-compatible setups,
    the fallback reads a Claude settings file and executes its ``apiKeyHelper`` command.
    The credential is returned only to the in-process Hermes SDK and is never emitted on
    the JSONL protocol.

    Args:
        request: Worker initialization message containing credential-source settings.

    Returns:
        The resolved credential, or ``None`` when the provider needs no explicit key.

    Raises:
        RuntimeError: If the configured environment variable, settings file, helper
            command, or helper output is unavailable or invalid.

    """
    if request.api_key_env:
        value = os.environ.get(request.api_key_env, "").strip()
        if not value:
            raise RuntimeError(f"credential environment variable {request.api_key_env!r} is unset")
        return value
    if not request.claude_settings:
        return None
    settings_path = Path(request.claude_settings).expanduser()
    try:
        settings = json.loads(settings_path.read_text())
        helper = str(settings["apiKeyHelper"]).strip()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"cannot load apiKeyHelper from Claude settings {settings_path}"
        ) from exc
    command = shlex.split(helper)
    if not command:
        raise RuntimeError("Claude apiKeyHelper is empty")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Claude apiKeyHelper failed") from exc
    credential = result.stdout.strip()
    if not credential:
        raise RuntimeError("Claude apiKeyHelper returned an empty credential")
    return credential


def configure_memory(request: WorkerInit) -> str | None:
    """Point the Hermes mem0 plugin at the configured self-hosted server.

    The plugin reads its settings from ``MEM0_*`` environment variables, so
    setting them here scopes the configuration to this worker process and lets
    each agent role carry its own ``agent_id``. ``MEM0_MODE`` is pinned so an
    ambient ``oss``-mode environment cannot silently disable memory.

    Args:
        request: Worker initialization message with optional memory settings.

    Returns:
        The resolved server credential (for diagnostic scrubbing), or ``None``
        when memory is disabled or the server needs no credential.

    Raises:
        RuntimeError: If the configured credential environment variable is unset.

    """
    if request.memory is None:
        return None
    api_key = None
    if request.memory.api_key_env:
        api_key = os.environ.get(request.memory.api_key_env, "").strip()
        if not api_key:
            raise RuntimeError(
                f"memory credential environment variable {request.memory.api_key_env!r} is unset"
            )
    os.environ["MEM0_MODE"] = "platform"
    os.environ["MEM0_HOST"] = request.memory.host
    os.environ["MEM0_USER_ID"] = request.memory.user_id
    os.environ["MEM0_AGENT_ID"] = request.memory.agent_id
    if api_key:
        os.environ["MEM0_API_KEY"] = api_key
    return api_key


def create_agent(request: WorkerInit, api_key: str | None) -> Any:
    """Construct a Hermes agent after registering configured MCP tools.

    Direct SDK use bypasses the Hermes CLI/TUI startup hook responsible for MCP
    discovery. Discovery must therefore happen before ``AIAgent`` snapshots its
    enabled toolsets.

    Args:
        request: Validated initialization settings for the worker.
        api_key: Credential resolved locally for the selected provider.

    Returns:
        Initialized Hermes ``AIAgent`` instance.

    """
    from tools.mcp_tool import (  # type: ignore[import-untyped]  # noqa: PLC0415
        discover_mcp_tools,
        mcp_prefixed_tool_name,
    )

    discovered = discover_mcp_tools()
    required = [toolset for toolset in request.toolsets if toolset.startswith("lassi-x-")]
    missing = [
        toolset
        for toolset in required
        if mcp_prefixed_tool_name(toolset, "write_file") not in discovered
    ]
    if missing:
        raise RuntimeError(
            "Hermes did not discover the required LASSI-X MCP workspace tools: "
            + ", ".join(missing)
        )
    from run_agent import AIAgent  # noqa: PLC0415

    toolsets = list(request.toolsets)
    if request.memory is not None and "memory" not in toolsets:
        # Hermes exposes external memory-provider tools (mem0_search, mem0_add,
        # ...) only when the "memory" toolset is enabled.
        toolsets.append("memory")
    return AIAgent(
        model=request.model,
        provider=request.provider,
        base_url=request.base_url,
        api_key=api_key,
        api_mode=request.api_mode,
        reasoning_config=(
            {"enabled": True, "effort": request.reasoning_effort}
            if request.reasoning_effort
            else None
        ),
        max_tokens=request.max_tokens,
        max_iterations=request.max_iterations,
        enabled_toolsets=toolsets,
        quiet_mode=True,
        skip_memory=request.memory is None,
        skip_context_files=True,
        save_trajectories=False,
        ephemeral_system_prompt=request.system_prompt,
    )


def shutdown_agent_memory(agent: Any | None, history: list[dict[str, Any]] | None) -> None:
    """Flush and close an agent's external memory provider.

    Hermes queues provider writes asynchronously after a completed turn. The
    SDK worker is the session boundary, so it must explicitly drain that queue
    before the process exits or the final turn's memories may be lost.

    Args:
        agent: Initialized Hermes agent, or ``None`` when initialization failed.
        history: Latest successful conversation history to pass to Hermes's
            session-end hooks.

    """
    if agent is None:
        return
    shutdown = getattr(agent, "shutdown_memory_provider", None)
    if callable(shutdown):
        shutdown(history or [])


def main() -> int:
    """Run the stateful Hermes SDK worker over a standard-input JSONL protocol.

    The worker accepts :class:`WorkerInit`, :class:`WorkerSend`, and
    :class:`WorkerClose` messages. One ``AIAgent`` and its conversation history
    persist across send operations, while token usage is reported as a per-turn
    delta. Malformed lines and operational exceptions are converted to
    :class:`WorkerFailure` responses so the parent process can record them as
    candidate diagnostics.

    Returns:
        Zero after receiving a close message or reaching end-of-input.

    """
    agent = None
    history: list[dict[str, Any]] | None = None
    previous_usage = (0, 0, 0.0)
    secrets: list[str] = []
    for line in sys.stdin:
        try:
            request = parse_worker_request(line)
        except ValidationError as exc:
            emit(WorkerFailure(error=f"ValidationError: {exc}"))
            continue
        try:
            if isinstance(request, WorkerInit):
                with contextlib.redirect_stdout(sys.stderr):
                    # Hermes emits import-time output; keep it away from the JSONL protocol.
                    api_key = resolve_api_key(request)
                    if api_key:
                        secrets.append(api_key)
                    memory_key = configure_memory(request)
                    if memory_key:
                        secrets.append(memory_key)
                    agent = create_agent(request, api_key)
                previous_usage = (
                    int(getattr(agent, "session_input_tokens", 0)),
                    int(getattr(agent, "session_output_tokens", 0)),
                    float(getattr(agent, "session_estimated_cost_usd", 0.0)),
                )
                emit(WorkerReady())
            elif isinstance(request, WorkerSend):
                if agent is None:
                    raise RuntimeError("worker has not been initialized")
                with contextlib.redirect_stdout(sys.stderr):
                    result = agent.run_conversation(
                        user_message=request.prompt,
                        conversation_history=history,
                    )
                failed = bool(result.get("failed", False))
                if not failed:
                    history = result.get("messages") or history
                current = (
                    int(getattr(agent, "session_input_tokens", 0)),
                    int(getattr(agent, "session_output_tokens", 0)),
                    float(getattr(agent, "session_estimated_cost_usd", 0.0)),
                )
                usage = TurnUsage(
                    input_tokens=max(0, current[0] - previous_usage[0]),
                    output_tokens=max(0, current[1] - previous_usage[1]),
                    estimated_cost_usd=max(0.0, current[2] - previous_usage[2]),
                )
                previous_usage = current
                if failed:
                    emit(
                        WorkerFailure(
                            error=scrub_sensitive(
                                str(result.get("error") or "Hermes conversation failed"),
                                secrets,
                            ),
                            usage=usage,
                        )
                    )
                else:
                    emit(
                        WorkerTurn(
                            text=result.get("final_response", ""),
                            usage=usage,
                            completed=bool(result.get("completed", False)),
                            exit_reason=str(result.get("turn_exit_reason") or "unknown"),
                        )
                    )
            else:
                break
        except BaseException as exc:  # worker must return a protocol error
            error = scrub_sensitive(f"{type(exc).__name__}: {exc}", secrets)
            trace = scrub_sensitive(traceback.format_exc()[-4000:], secrets)
            emit(
                WorkerFailure(
                    error=error,
                    traceback=trace,
                )
            )
    try:
        with contextlib.redirect_stdout(sys.stderr):
            shutdown_agent_memory(agent, history)
    except BaseException as exc:  # cleanup must never corrupt the JSONL protocol
        error = scrub_sensitive(f"{type(exc).__name__}: {exc}", secrets)
        print(f"Hermes memory shutdown failed: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
