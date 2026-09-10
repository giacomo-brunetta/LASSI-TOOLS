"""Preflight the LLM endpoint before a run or a benchmark matrix is launched.

``execution doctor`` verifies the Academy/Globus side. Nothing verified the model
endpoint, so a dead proxy or a wrong model identifier was only discovered one
kernel at a time, each costing a minute or two of silent failure.

The probe deliberately replays a tool call. Argo accepts a plain completion for
model identifiers that still reject ``messages[].tool_calls`` during history
replay, so a "hello" probe would pass and the suite would fail anyway on the
first agent turn. Sending an assistant ``tool_calls`` message plus its matching
``tool`` result reproduces the exact request shape the agent loop uses.

A 200 is also not sufficient. Argo answers an unknown identifier with a fallback
model rather than an error, so the probe compares the ``model`` the response
reports serving against the one requested; otherwise a typo produces a full set
of measurements labelled with a model that never ran.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Literal

import httpx

from .config import StrictModel
from .hermes_worker import resolve_api_key
from .protocol import WorkerInit

if TYPE_CHECKING:
    from .config import ModelConfig

# A preflight competes with nothing and gates everything, so it must be short
# enough that a wedged endpoint is reported in seconds rather than minutes.
DEFAULT_TIMEOUT_S = 20.0

Reason = Literal[
    "ok",
    "endpoint_unreachable",
    "auth_failed",
    "unknown_model",
    "tool_call_replay_unsupported",
    "endpoint_path_not_found",
    "model_substituted",
    "rate_limited",
    "bad_request",
    "server_error",
    "credential_error",
    "unexpected_response",
]

# One tool plus a completed call/result pair. The identifier is echoed in both
# the assistant message and the tool result because providers reject a result
# whose tool_call_id does not match an in-history call.
_PROBE_CALL_ID = "lassi_x_preflight_0"

_PROBE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lassi_x_preflight",
            "description": "No-op tool used only to validate tool-call replay.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    }
]

_PROBE_MESSAGES = [
    {"role": "user", "content": "Call lassi_x_preflight."},
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": _PROBE_CALL_ID,
                "type": "function",
                "function": {"name": "lassi_x_preflight", "arguments": "{}"},
            }
        ],
    },
    {"role": "tool", "tool_call_id": _PROBE_CALL_ID, "content": "ok"},
    {"role": "user", "content": "Reply with the single word: ready"},
]


class ProbeReport(StrictModel):
    """Outcome of one model-endpoint probe.

    Attributes:
        ok: Whether the endpoint answered a tool-call replay successfully.
        model: Model identifier that was probed.
        base_url: Endpoint the probe was sent to.
        reason: Machine-readable classification of the outcome.
        detail: Provider or transport text explaining a failure.
        hint: Operator-facing next step, empty when the probe passed.
        status_code: HTTP status, absent when the request never completed.
        elapsed_s: Wall time spent on the probe.
        resolved_model: Identifier the endpoint reported serving, which is the
            provenance the paper needs and is not always the one requested.
    """

    ok: bool
    model: str
    base_url: str | None
    reason: Reason
    detail: str = ""
    hint: str = ""
    status_code: int | None = None
    elapsed_s: float = 0.0
    resolved_model: str | None = None


def _endpoint(base_url: str) -> str:
    """Build the chat-completions URL exactly as the agent's client will.

    Hermes passes ``base_url`` to the OpenAI SDK, which appends the suffix
    verbatim, so this does the same. An earlier version inserted a missing
    ``/v1`` for the caller and thereby reported a healthy endpoint for a
    configuration under which every agent turn 404s -- the precise false
    confidence this preflight exists to prevent. A probe that repairs its own
    input is not testing the configuration.

    Args:
        base_url: Configured provider base URL.

    Returns:
        Absolute chat-completions URL.
    """
    return f"{base_url.rstrip('/')}/chat/completions"


def _error_fields(body: str) -> tuple[str, str, str]:
    """Extract provider error text from a response body.

    Args:
        body: Raw response text.

    Returns:
        Triple of message, ``param``, and ``code``; the message falls back to
        the raw body when it is not an OpenAI-style error envelope.
    """
    try:
        error = json.loads(body).get("error", {})
    except (json.JSONDecodeError, AttributeError):
        return body.strip()[:500], "", ""
    if not isinstance(error, dict):
        return body.strip()[:500], "", ""
    return (
        str(error.get("message", "")).strip() or body.strip()[:500],
        str(error.get("param", "")),
        str(error.get("code", "")),
    )


def _internal_id_hint(model: str) -> str:
    """Build the hint for identifiers Argo does not accept.

    Args:
        model: Model identifier that was rejected.

    Returns:
        Guidance naming the internal-identifier requirement.
    """
    return (
        f"{model!r} was rejected. Argo needs its internal model ID "
        "(for example 'gpt56sol' or 'claudeopus5'), not a display name; "
        "set endpoint_model in the affected run configuration."
    )


def _resolved_model(body: str) -> str:
    """Read back the identifier the endpoint says it actually served.

    Args:
        body: Raw success-response text.

    Returns:
        The response's ``model`` field, or an empty string when the body is not
        JSON or omits it.
    """
    try:
        served = json.loads(body).get("model", "")
    except (json.JSONDecodeError, AttributeError):
        return ""
    return str(served) if isinstance(served, str) else ""


def _normalize(model: str) -> str:
    """Reduce a model identifier to a comparable form.

    Argo names the same model several ways -- ``gpt56sol`` requested,
    ``gpt-5.6-sol-2026-07-09`` served -- so punctuation and case carry no
    meaning for an identity check.

    Args:
        model: Any model identifier.

    Returns:
        The identifier lowercased with non-alphanumerics removed.
    """
    return "".join(character for character in model.lower() if character.isalnum())


def _is_same_model(requested: str, served: str) -> bool:
    """Decide whether a served identifier is the requested model.

    A served identifier normally extends the requested one with a version date,
    or drops one the caller supplied, so either may be a prefix of the other.
    This is a heuristic: a requested identifier short enough to prefix an
    unrelated model would pass, which is why the failure it guards names both
    identifiers rather than asserting what went wrong.

    Args:
        requested: Identifier sent in the request.
        served: Identifier the endpoint reported back.

    Returns:
        Whether the two plausibly name the same model.
    """
    left, right = _normalize(requested), _normalize(served)
    if not left or not right:
        return True
    return left.startswith(right) or right.startswith(left)


def _classify(model: str, status: int, body: str) -> tuple[Reason, str, str]:
    """Map an HTTP failure onto a reason and an operator hint.

    Args:
        model: Model identifier that was probed.
        status: HTTP status code returned by the endpoint.
        body: Raw response body.

    Returns:
        Triple of reason, detail text, and hint.
    """
    message, param, code = _error_fields(body)
    if status in (401, 403):
        return (
            "auth_failed",
            message,
            "The endpoint rejected the credential. Check apiKeyHelper in the "
            "configured claude_settings file, or the api_key_env variable.",
        )
    if status == 429:
        return "rate_limited", message, "The endpoint is rate limiting; retry later."
    # Checked before the generic 400 branch: a tool_calls rejection is a model
    # capability problem, not a malformed request, and has a specific fix.
    if "tool_calls" in param or "tool_calls" in message:
        return "tool_call_replay_unsupported", message, _internal_id_hint(model)
    names_a_model = code == "model_not_found" or "model" in param
    # A 404 that says nothing about a model is the address being wrong, not the
    # identifier. The usual cause is a base_url missing its version prefix, which
    # the SDK turns into "<base>/chat/completions" and the shim does not serve.
    if status == 404 and not names_a_model:
        return (
            "endpoint_path_not_found",
            message,
            "The endpoint has no chat-completions route at this address. base_url "
            "is used verbatim with '/chat/completions' appended, so it usually needs "
            "to end in '/v1' (for example 'http://127.0.0.1:52226/v1').",
        )
    if status == 404 or names_a_model:
        return "unknown_model", message, _internal_id_hint(model)
    if status >= 500:
        return (
            "server_error",
            message,
            "The endpoint is up but failing internally; check the proxy's own logs.",
        )
    return "bad_request", message, "The endpoint rejected the probe request."


async def probe_model(
    model: ModelConfig,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ProbeReport:
    """Send one tool-call replay to a model endpoint and classify the outcome.

    Args:
        model: Model configuration naming the endpoint, identifier, and credential source.
        timeout_s: Ceiling for the probe request.
        transport: Injected HTTPX transport, used by tests.

    Returns:
        A report describing whether the endpoint is usable and, when it is not,
        why and what to do about it.
    """
    base_url = model.base_url
    if not base_url:
        return ProbeReport(
            ok=False,
            model=model.model,
            base_url=None,
            reason="endpoint_unreachable",
            detail="no base_url configured",
            hint="Set base_url on the model configuration.",
        )
    if model.api_mode not in (None, "chat_completions"):
        # Only the chat-completions shape is exercised here; probing a mode the
        # suite does not use would report failures that do not matter.
        return ProbeReport(
            ok=True,
            model=model.model,
            base_url=base_url,
            reason="ok",
            detail=f"probe skipped for api_mode {model.api_mode!r}",
        )

    try:
        api_key = resolve_api_key(
            WorkerInit(
                model=model.model,
                api_key_env=model.api_key_env,
                claude_settings=(
                    str(model.claude_settings.expanduser()) if model.claude_settings else None
                ),
                role="preflight",
            )
        )
    except RuntimeError as exc:
        return ProbeReport(
            ok=False,
            model=model.model,
            base_url=base_url,
            reason="credential_error",
            detail=str(exc),
            hint="The credential source failed before any request was sent.",
        )

    payload: dict[str, Any] = {
        "model": model.model,
        "messages": _PROBE_MESSAGES,
        "tools": _PROBE_TOOLS,
        # Enough for one word; the probe validates acceptance, not generation.
        "max_tokens": 16,
    }
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    # Timed here rather than read from response.elapsed, which httpx only
    # populates for responses it streamed itself.
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout_s, transport=transport) as client:
        try:
            response = await client.post(_endpoint(base_url), json=payload, headers=headers)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            return ProbeReport(
                ok=False,
                model=model.model,
                base_url=base_url,
                reason="endpoint_unreachable",
                detail=str(exc),
                hint=(
                    f"Nothing is answering at {base_url}. Start the LLM proxy, or point "
                    "the suite elsewhere with LASSI_PAPER_LLM_BASE_URL."
                ),
            )
        except httpx.HTTPError as exc:
            return ProbeReport(
                ok=False,
                model=model.model,
                base_url=base_url,
                reason="endpoint_unreachable",
                detail=f"{type(exc).__name__}: {exc}",
                hint=f"The probe to {base_url} did not complete within {timeout_s:.0f}s.",
            )
        elapsed = time.perf_counter() - started
        body = response.text

    if response.is_success:
        served = _resolved_model(body)
        # A 200 is not proof the right model answered. Argo serves an unknown
        # identifier with a fallback model instead of rejecting it, so a typo
        # yields real measurements attributed to a model that never ran.
        substituted = not _is_same_model(model.model, served)
        return ProbeReport(
            ok=not substituted,
            model=model.model,
            base_url=base_url,
            reason="model_substituted" if substituted else "ok",
            detail=(
                f"requested {model.model!r} but the endpoint served {served!r}"
                if substituted
                else ""
            ),
            hint=(
                f"{model.model!r} is not a known identifier, so the endpoint "
                f"silently fell back to {served!r}. Benchmarks would be labelled "
                f"with a model that never ran. Set endpoint_model in the affected "
                f"run configuration to the served identifier, or "
                f"to the correct internal ID (for example 'gpt56sol' or 'claudeopus5')."
                if substituted
                else ""
            ),
            status_code=response.status_code,
            elapsed_s=round(elapsed, 3),
            resolved_model=served or None,
        )
    reason, detail, hint = _classify(model.model, response.status_code, body)
    return ProbeReport(
        ok=False,
        model=model.model,
        base_url=base_url,
        reason=reason,
        detail=detail,
        hint=hint,
        status_code=response.status_code,
        elapsed_s=round(elapsed, 3),
    )


def distinct_models(models: Any) -> list[ModelConfig]:
    """Collapse a run's model roles down to the endpoints worth probing.

    The paper configs give planner, candidates, and compensation identical model
    blocks, so probing each role would send five identical requests.

    Args:
        models: A :class:`~lassi_x.config.ModelsConfig` instance.

    Returns:
        One entry per distinct endpoint/identifier/credential combination, in
        first-seen order.
    """
    seen: set[tuple[Any, ...]] = set()
    unique = []
    for entry in [models.planner, *models.candidates, models.compensation]:
        key = (entry.base_url, entry.model, entry.api_mode, entry.api_key_env)
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique
