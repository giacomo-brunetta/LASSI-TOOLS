"""In-container agent runner.

The host-side graph orchestrator launches one of these per agent dispatch
via `docker exec`. Payload arrives base64-encoded JSON on argv so we don't
have to stream stdin through docker-py's low-level API; the result comes
back as a single-line JSON envelope on stdout that the host parses.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/opt/lassi")

from agents import AGENT_REGISTRY, set_dispatch_backend  # noqa: E402

RESULT_SENTINEL = "__LASSI_RESULT__"


def _decode(obj):
    """Inverse of the host-side encoder: turn {"__type__": "Path"} back into Path."""
    if isinstance(obj, dict):
        if obj.get("__type__") == "Path":
            return Path(obj["value"])
        return {k: _decode(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode(x) for x in obj]
    return obj


async def _run(agent_name: str, payload: dict) -> str:
    # Make sure we never recurse into a backend inside the container.
    set_dispatch_backend(None)

    cls = AGENT_REGISTRY.get(agent_name)
    if cls is None:
        raise KeyError(f"unknown agent {agent_name!r}; known: {sorted(AGENT_REGISTRY)}")
    agent = cls()
    context = payload.pop("context", {})
    return await agent.dispatch_agent(**payload, **context)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one agent dispatch inside this container.")
    parser.add_argument("--agent", required=True, help="Agent name from AGENT_REGISTRY.")
    parser.add_argument(
        "--payload-b64",
        required=True,
        help="Base64-encoded JSON payload (cwd, allowed_paths, model, permission_mode, context).",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(levelname)s:%(name)s:%(message)s",
        # Send logs to stderr so stdout is reserved for the result envelope.
        stream=sys.stderr,
        force=True,
    )

    try:
        raw = base64.b64decode(args.payload_b64).decode("utf-8")
        payload = _decode(json.loads(raw))
    except Exception as exc:
        sys.stderr.write(f"payload decode failed: {exc}\n")
        return 2

    try:
        result = asyncio.run(_run(args.agent, payload))
    except Exception as exc:
        sys.stderr.write("agent dispatch failed:\n")
        traceback.print_exc(file=sys.stderr)
        envelope = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        sys.stdout.write(f"{RESULT_SENTINEL}{json.dumps(envelope)}\n")
        sys.stdout.flush()
        return 1

    envelope = {"ok": True, "result": result}
    sys.stdout.write(f"{RESULT_SENTINEL}{json.dumps(envelope)}\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
