from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from lassi_x.config import ModelConfig, ModelsConfig
from lassi_x.model_doctor import distinct_models, probe_model

# The literal body Argo returned on 2026-08-05, when the configs still carried
# display names. It cost ten runs before anyone read a run directory.
TOOL_CALL_REPLAY_BODY = json.dumps(
    {
        "error": {
            "message": "Unknown parameter: 'messages[0].tool_calls'.",
            "type": "invalid_request_error",
            "param": "messages[0].tool_calls",
            "code": "unknown_parameter",
        }
    }
)

SUCCESS_BODY = json.dumps({"choices": [{"message": {"role": "assistant", "content": "ready"}}]})


def _model(**overrides: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "model": "claudeopus5",
        "provider": "custom",
        "base_url": "http://127.0.0.1:52226",
        "api_mode": "chat_completions",
    }
    return ModelConfig(**{**defaults, **overrides})  # type: ignore[arg-type]


def _probe(handler: object, **overrides: object) -> object:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return asyncio.run(probe_model(_model(**overrides), transport=transport, timeout_s=5))


def _responder(status: int, body: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=body)

    return handler


@pytest.mark.parametrize(
    ("status", "body", "reason"),
    [
        (400, TOOL_CALL_REPLAY_BODY, "tool_call_replay_unsupported"),
        (404, json.dumps({"error": {"message": "no such model"}}), "unknown_model"),
        (
            400,
            json.dumps({"error": {"message": "bad model", "code": "model_not_found"}}),
            "unknown_model",
        ),
        (401, json.dumps({"error": {"message": "unauthorized"}}), "auth_failed"),
        (403, json.dumps({"error": {"message": "forbidden"}}), "auth_failed"),
        (429, json.dumps({"error": {"message": "slow down"}}), "rate_limited"),
        (503, json.dumps({"error": {"message": "upstream down"}}), "server_error"),
        (400, json.dumps({"error": {"message": "malformed"}}), "bad_request"),
    ],
)
def test_classifies_http_failures(status: int, body: str, reason: str) -> None:
    report = _probe(_responder(status, body))
    assert report.ok is False
    assert report.reason == reason
    assert report.status_code == status
    assert report.detail
    assert report.hint


def test_tool_call_rejection_names_the_internal_id_fix() -> None:
    report = _probe(_responder(400, TOOL_CALL_REPLAY_BODY), model="GPT-5.6 Sol")
    assert report.reason == "tool_call_replay_unsupported"
    assert "gpt56sol" in report.hint


def test_successful_probe_reports_ok() -> None:
    report = _probe(_responder(200, SUCCESS_BODY))
    assert report.ok is True
    assert report.reason == "ok"
    assert report.status_code == 200


def test_probe_replays_a_tool_call() -> None:
    """A plain completion passes on endpoints that still reject replay."""
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, text=SUCCESS_BODY)

    _probe(handler)
    roles = [message["role"] for message in seen["messages"]]  # type: ignore[index]
    assert "assistant" in roles
    assert "tool" in roles
    assistant = next(m for m in seen["messages"] if m["role"] == "assistant")  # type: ignore[index]
    assert assistant["tool_calls"]
    assert seen["tools"]


def test_unreachable_endpoint_is_reported_without_a_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("All connection attempts failed", request=request)

    report = _probe(handler)
    assert report.ok is False
    assert report.reason == "endpoint_unreachable"
    assert report.status_code is None
    assert "LASSI_PAPER_LLM_BASE_URL" in report.hint


def test_missing_base_url_fails_before_any_request() -> None:
    report = asyncio.run(probe_model(_model(base_url=None)))
    assert report.ok is False
    assert report.reason == "endpoint_unreachable"


def test_probe_targets_the_chat_completions_path() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, text=SUCCESS_BODY)

    _probe(handler)
    assert seen == ["http://127.0.0.1:52226/v1/chat/completions"]

    seen.clear()
    _probe(handler, base_url="http://127.0.0.1:52226/v1")
    assert seen == ["http://127.0.0.1:52226/v1/chat/completions"]


def _served(model: str) -> str:
    """Build a success body echoing the identifier the endpoint served."""
    return json.dumps(
        {"model": model, "choices": [{"message": {"role": "assistant", "content": "ready"}}]}
    )


@pytest.mark.parametrize(
    ("requested", "served"),
    [
        # Observed on the live shim 2026-08-07: an unknown identifier is answered
        # by a fallback model with a 200, not rejected.
        ("claudeopus99", "gpt-5.4-nano-2026-03-17"),
        ("GPT-5.6", "gpt-5.4-nano-2026-03-17"),
    ],
)
def test_silent_model_substitution_fails_the_probe(requested: str, served: str) -> None:
    report = _probe(_responder(200, _served(served)), model=requested)
    assert report.ok is False
    assert report.reason == "model_substituted"
    assert report.status_code == 200
    assert report.resolved_model == served
    assert served in report.hint


@pytest.mark.parametrize(
    ("requested", "served"),
    [
        ("gpt56sol", "gpt-5.6-sol-2026-07-09"),  # served adds a version date
        ("claudeopus5", "claude-opus-5"),  # differs only in punctuation
        ("GPT-5.6 Sol", "gpt-5.6-sol-2026-07-09"),  # display name resolves correctly
        ("claudeopus5", ""),  # endpoint omits the field; nothing to check
    ],
)
def test_matching_identifiers_pass(requested: str, served: str) -> None:
    body = _served(served) if served else SUCCESS_BODY
    report = _probe(_responder(200, body), model=requested)
    assert report.ok is True
    assert report.reason == "ok"


def test_distinct_models_collapses_identical_roles() -> None:
    """The paper configs repeat one model block five times; probe it once."""
    entry = _model()
    models = ModelsConfig(planner=entry, candidates=[entry, entry, entry], compensation=entry)
    assert len(distinct_models(models)) == 1

    other = _model(model="gpt56sol")
    mixed = ModelsConfig(planner=entry, candidates=[other], compensation=entry)
    assert [item.model for item in distinct_models(mixed)] == ["claudeopus5", "gpt56sol"]
