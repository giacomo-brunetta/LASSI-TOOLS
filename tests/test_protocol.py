from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from lassi_x.protocol import (
    ExecRequest,
    ExecResult,
    FileGet,
    FilePut,
    ListDir,
    MemorySettings,
    TurnUsage,
    WorkerFailure,
    WorkerInit,
    WorkerReady,
    WorkerSend,
    WorkerTurn,
    parse_worker_request,
    parse_worker_response,
)


def test_worker_request_round_trip_preserves_discriminated_types() -> None:
    init = WorkerInit(model="gpt-x", role="planner", toolsets=["skills"])
    send = WorkerSend(prompt="translate the kernel")
    for message in (init, send):
        parsed = parse_worker_request(message.model_dump_json())
        assert parsed == message


def test_worker_request_rejects_unknown_operation_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        parse_worker_request('{"op": "reboot"}')
    with pytest.raises(ValidationError):
        parse_worker_request('{"op": "send", "prompt": "x", "shell": true}')
    with pytest.raises(ValidationError):
        parse_worker_request("not json")


def test_worker_response_round_trip_and_failure_parsing() -> None:
    turn = WorkerTurn(text="done", usage=TurnUsage(input_tokens=3, output_tokens=5))
    assert parse_worker_response(turn.model_dump_json()) == turn
    parsed = parse_worker_response('{"kind": "error", "error": "boom"}')
    assert isinstance(parsed, WorkerFailure)
    assert parsed.error == "boom"
    assert isinstance(parse_worker_response('{"kind": "ready"}'), WorkerReady)


def test_wire_messages_are_immutable() -> None:
    message = WorkerSend(prompt="x")
    with pytest.raises(ValidationError):
        message.prompt = "y"  # type: ignore[misc]


@pytest.mark.parametrize(
    "path",
    ["/etc/passwd", "../escape", "a/../../b", "a\\b", "", "./candidate.py", "a//b"],
)
def test_workspace_paths_reject_absolute_escaping_or_unnormalized(path: str) -> None:
    with pytest.raises(ValidationError):
        FileGet(workspace="c1", path=path)
    with pytest.raises(ValidationError):
        ListDir(workspace="c1", path=path)


def test_workspace_paths_accept_normalized_relative_forms() -> None:
    assert FileGet(workspace="c1", path="candidate.py").path == "candidate.py"
    assert FileGet(workspace="c1", path="sub/dir/out.csv").path == "sub/dir/out.csv"
    assert ListDir(workspace="c1").path == "."


def test_workspace_names_are_constrained() -> None:
    with pytest.raises(ValidationError):
        ListDir(workspace="../c1")
    with pytest.raises(ValidationError):
        ListDir(workspace="")


def test_file_put_requires_exactly_one_payload() -> None:
    FilePut(workspace="c1", path="candidate.py", text="print()")
    FilePut(workspace="c1", path="blob.bin", content_b64="AAAA")
    with pytest.raises(ValidationError):
        FilePut(workspace="c1", path="candidate.py")
    with pytest.raises(ValidationError):
        FilePut(workspace="c1", path="candidate.py", text="x", content_b64="AAAA")


def test_exec_request_validates_argv_cwd_and_timeout() -> None:
    request = ExecRequest(workspace="c1", argv=["python", "-m", "py_compile", "candidate.py"])
    assert request.timeout_s == 600.0
    with pytest.raises(ValidationError):
        ExecRequest(workspace="c1", argv=[])
    with pytest.raises(ValidationError):
        ExecRequest(workspace="c1", argv=[""])
    with pytest.raises(ValidationError):
        ExecRequest(workspace="c1", argv=["ls"], cwd="/tmp")
    with pytest.raises(ValidationError):
        ExecRequest(workspace="c1", argv=["ls"], timeout_s=0.0)


def test_exec_result_ok_requires_zero_exit_within_deadline() -> None:
    assert ExecResult(workspace="c1", exit_code=0, duration_s=0.1).ok
    assert not ExecResult(workspace="c1", exit_code=1, duration_s=0.1).ok
    assert not ExecResult(workspace="c1", exit_code=0, timed_out=True, duration_s=9.0).ok
    assert not ExecResult(workspace="c1", exit_code=None, duration_s=0.0).ok


def _run_worker(stdin: str) -> subprocess.CompletedProcess[str]:
    package_root = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_root) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "lassi_x.hermes_worker"],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        check=False,
    )


def test_worker_process_speaks_typed_protocol_for_errors_and_close() -> None:
    lines = [
        "garbage",
        WorkerSend(prompt="hello").model_dump_json(),
        '{"op": "close"}',
    ]
    completed = _run_worker("\n".join(lines) + "\n")
    assert completed.returncode == 0
    responses = [parse_worker_response(line) for line in completed.stdout.splitlines()]
    assert len(responses) == 2
    assert isinstance(responses[0], WorkerFailure)
    assert "ValidationError" in responses[0].error
    assert isinstance(responses[1], WorkerFailure)
    assert "worker has not been initialized" in responses[1].error


def test_worker_init_memory_settings_round_trip() -> None:
    init = WorkerInit(
        model="gpt-x",
        role="c1",
        toolsets=["skills", "lassi-x-c1"],
        memory=MemorySettings(
            host="http://localhost:8888",
            api_key_env="MEM0_API_KEY",
            user_id="lassi-x",
            agent_id="c1",
        ),
    )
    parsed = parse_worker_request(init.model_dump_json())
    assert parsed == init
    assert isinstance(parsed, WorkerInit)
    assert parsed.memory is not None
    assert parsed.memory.agent_id == "c1"


def test_worker_init_memory_rejects_credential_material() -> None:
    with pytest.raises(ValidationError):
        MemorySettings(
            host="http://localhost:8888",
            api_key="sk-secret",  # type: ignore[call-arg]
            user_id="lassi-x",
            agent_id="c1",
        )
