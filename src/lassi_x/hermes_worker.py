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

PROTOCOL_STREAM = sys.stdout


def emit(payload: dict[str, Any]) -> None:
    """Write one response object to the worker's JSONL protocol stream.

    Args:
        payload: JSON-serializable response returned to the parent session.

    """
    PROTOCOL_STREAM.write(json.dumps(payload) + "\n")
    PROTOCOL_STREAM.flush()


def resolve_api_key(request: dict[str, Any]) -> str | None:
    """Resolve an API credential from the configured external source.

    Environment-variable configuration takes precedence. For Argo-compatible setups,
    the fallback reads a Claude settings file and executes its ``apiKeyHelper`` command.
    The credential is returned only to the in-process Hermes SDK and is never emitted on
    the JSONL protocol.

    Args:
        request: Worker initialization request containing credential-source settings.

    Returns:
        The resolved credential, or ``None`` when the provider needs no explicit key.

    Raises:
        RuntimeError: If the configured environment variable, settings file, helper
            command, or helper output is unavailable or invalid.

    """
    env_name = request.get("api_key_env")
    if env_name:
        value = os.environ.get(str(env_name), "").strip()
        if not value:
            raise RuntimeError(f"credential environment variable {env_name!r} is unset")
        return value
    settings_value = request.get("claude_settings")
    if not settings_value:
        return None
    settings_path = Path(str(settings_value)).expanduser()
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


def main() -> int:
    """Run the stateful Hermes SDK worker over a standard-input JSONL protocol.

    The worker accepts ``init``, ``send``, and ``close`` operations. One ``AIAgent`` and
    its conversation history persist across send operations, while token usage is
    reported as a per-turn delta. Operational exceptions are converted to protocol error
    responses so the parent process can record them as candidate diagnostics.

    Returns:
        Zero after receiving a close operation or reaching end-of-input.

    """
    agent = None
    history: list[dict[str, Any]] | None = None
    previous_usage = (0, 0, 0.0)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            op = request.get("op")
            if op == "init":
                with contextlib.redirect_stdout(sys.stderr):
                    # Hermes emits import-time output; keep it away from the JSONL protocol.
                    from run_agent import AIAgent  # noqa: PLC0415

                    api_key = resolve_api_key(request)
                    agent = AIAgent(
                        model=request["model"],
                        provider=request.get("provider"),
                        base_url=request.get("base_url"),
                        api_key=api_key,
                        api_mode=request.get("api_mode"),
                        max_tokens=int(request.get("max_tokens", 16_384)),
                        max_iterations=int(request.get("max_iterations", 90)),
                        enabled_toolsets=request.get("toolsets") or [],
                        quiet_mode=True,
                        skip_memory=True,
                        skip_context_files=True,
                        save_trajectories=False,
                        ephemeral_system_prompt=request.get("system_prompt"),
                    )
                previous_usage = (
                    int(getattr(agent, "session_input_tokens", 0)),
                    int(getattr(agent, "session_output_tokens", 0)),
                    float(getattr(agent, "session_estimated_cost_usd", 0.0)),
                )
                emit({"ok": True})
            elif op == "send":
                if agent is None:
                    raise RuntimeError("worker has not been initialized")
                with contextlib.redirect_stdout(sys.stderr):
                    result = agent.run_conversation(
                        user_message=request["prompt"],
                        conversation_history=history,
                    )
                history = result.get("messages") or history
                current = (
                    int(getattr(agent, "session_input_tokens", 0)),
                    int(getattr(agent, "session_output_tokens", 0)),
                    float(getattr(agent, "session_estimated_cost_usd", 0.0)),
                )
                usage = {
                    "input_tokens": max(0, current[0] - previous_usage[0]),
                    "output_tokens": max(0, current[1] - previous_usage[1]),
                    "estimated_cost_usd": max(0.0, current[2] - previous_usage[2]),
                }
                previous_usage = current
                emit({"ok": True, "text": result.get("final_response", ""), "usage": usage})
            elif op == "close":
                break
            else:
                raise ValueError(f"unknown worker operation: {op!r}")
        except BaseException as exc:  # worker must return a protocol error
            emit(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-4000:],
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
