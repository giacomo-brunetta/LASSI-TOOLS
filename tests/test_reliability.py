"""Regressions for process lifecycle, transport ambiguity, and evidence validation."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import os
import pickle
import signal
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from lassi_x.compatibility.target import load_target
from lassi_x.config import EquivalenceConfig, ModelConfig, RunConfig
from lassi_x.execution import ExecutionContext
from lassi_x.execution.workspace import run_exec
from lassi_x.hermes import HermesSession
from lassi_x.protocol import MAX_INLINE_BYTES, ExecRequest, FilePut, parse_worker_request
from lassi_x.worker_results import validate_worker_result

from .test_config import minimal_config


def session_at(path: Path, **settings: Any) -> HermesSession:
    return HermesSession(
        ModelConfig(model="test", turn_retries=0, **settings),
        cwd=path,
        system_prompt="",
        toolsets=[],
        role="test",
    )


def fake_worker(monkeypatch: pytest.MonkeyPatch, code: str) -> list[dict[str, Any]]:
    launch = asyncio.create_subprocess_exec
    launches: list[dict[str, Any]] = []

    async def create(*args: Any, **kwargs: Any) -> asyncio.subprocess.Process:
        launches.append(kwargs)
        return await launch(sys.executable, "-u", "-c", code, **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    return launches


@pytest.mark.asyncio
async def test_verbose_worker_does_not_deadlock_and_retains_bounded_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_worker(
        monkeypatch,
        """
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request['op'] == 'init':
        sys.stderr.write('x' * 2000000)
        sys.stderr.flush()
        print('{"kind":"ready"}', flush=True)
    elif request['op'] == 'send':
        print('{"kind":"turn","text":"done","usage":{}}', flush=True)
    else:
        break
""",
    )
    session = session_at(tmp_path, turn_timeout_s=2)
    try:
        assert (await asyncio.wait_for(session.send("go"), 3)).text == "done"
        assert len(session._stderr_tail) <= 4000
    finally:
        await session.close()
    assert session._stderr_task is None
    assert session._profile is None


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", ["startup", "write"])
async def test_turn_deadline_includes_startup_and_request_write(
    tmp_path: Path, phase: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = session_at(tmp_path, turn_timeout_s=0.02)
    closed = False

    async def hang(*args: Any) -> None:
        await asyncio.sleep(30)

    async def ready() -> None:
        return None

    async def close() -> None:
        nonlocal closed
        closed = True

    monkeypatch.setattr(session, "start", hang if phase == "startup" else ready)
    monkeypatch.setattr(session, "_write", hang)
    monkeypatch.setattr(session, "close", close)
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(session.send("go"), 0.5)
    assert closed


@pytest.mark.asyncio
async def test_worker_profiles_are_isolated_and_explicit_home_is_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.yaml").write_text("custom: true\n")
    launches = fake_worker(
        monkeypatch,
        """
import json, sys
for line in sys.stdin:
    if json.loads(line)['op'] == 'close': break
    print('{"kind":"ready"}', flush=True)
""",
    )
    sessions = [session_at(tmp_path), session_at(tmp_path)]
    for session in sessions:
        session.hermes_home = source
    profiles: list[Path] = []
    try:
        for session in sessions:
            await session.start()
        profiles = [Path(item["env"]["HERMES_HOME"]) for item in launches]
        assert profiles[0] != profiles[1]
        assert all(path != source for path in profiles)
        assert all((path / "config.yaml").read_text() == "custom: true\n" for path in profiles)
        assert (source / "config.yaml").read_text() == "custom: true\n"
    finally:
        for session in sessions:
            await session.close()
    assert all(not path.exists() for path in profiles)


@pytest.mark.asyncio
async def test_execution_cancellation_kills_and_reaps_child(tmp_path: Path) -> None:
    pidfile = tmp_path / "pid"
    task = asyncio.create_task(
        run_exec(
            tmp_path,
            ExecRequest(
                workspace="w",
                argv=[
                    sys.executable,
                    "-c",
                    (
                        f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); '
                        "time.sleep(30)"
                    ),
                ],
            ),
        )
    )
    pid = None
    try:
        async with asyncio.timeout(3):
            while not pidfile.exists():
                await asyncio.sleep(0.01)
        pid = int(pidfile.read_text())
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    finally:
        task.cancel()
        if pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(pid, signal.SIGKILL)


@pytest.mark.asyncio
async def test_cleanup_failure_does_not_skip_server_shutdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = await ExecutionContext.start(
        RunConfig.model_validate(minimal_config(tmp_path)), tmp_path
    )
    context.register_workspace("c1")
    stopped = False
    stop = context.runner.stop

    def fail(*args: Any, **kwargs: Any) -> None:
        raise OSError("read-only configuration")

    async def record_stop() -> None:
        nonlocal stopped
        stopped = True
        await stop()

    monkeypatch.setattr("lassi_x.hermes_config.unregister_workspace_servers", fail)
    monkeypatch.setattr(context.runner, "stop", record_stop)
    await context.close()
    assert stopped


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_correctness_tolerances_must_be_finite(value: float) -> None:
    with pytest.raises(ValidationError):
        EquivalenceConfig(rtol=value)


def test_config_updates_are_validated() -> None:
    config = ModelConfig(model="test")
    with pytest.raises(ValidationError):
        config.max_iterations = -1
    with pytest.raises(ValidationError):
        config.validated_update(max_iterations=-1)


def test_wire_collections_are_immutable_and_serializable() -> None:
    command = ["true"]
    request = ExecRequest(workspace="w", argv=command, env={"X": "1"})
    command.clear()
    assert request.argv == ["true"]
    with pytest.raises(TypeError):
        request.argv.clear()
    with pytest.raises(TypeError):
        request.env["X"] = "2"
    assert pickle.loads(pickle.dumps(request)) == request
    assert ExecRequest.model_validate_json(request.model_dump_json()) == request
    assert request.model_copy(deep=True) == request


def test_payload_limits_count_utf8_and_decoded_bytes() -> None:
    with pytest.raises(ValidationError):
        FilePut(workspace="w", path="x", text="😀" * (MAX_INLINE_BYTES // 4 + 1))
    with pytest.raises(ValidationError):
        FilePut(
            workspace="w",
            path="x",
            content_b64=base64.b64encode(b"x" * (MAX_INLINE_BYTES + 1)).decode(),
        )


def test_protocol_frames_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lassi_x.protocol.MAX_FRAME_BYTES", 32)
    with pytest.raises(ValueError, match="frame"):
        parse_worker_request('{"op":"send","prompt":"' + "x" * 33 + '"}')


@pytest.mark.parametrize(
    "payload",
    [
        {"ok": "false"},
        {"ok": True, "valid": "false"},
        {"ok": True, "timing": {"cuda_synchronized": "false"}},
        {"ok": True, "timing": {"sample_count": True}},
        {"ok": True, "median_s": float("inf")},
        {"ok": True, "evaluation_output": {"semantic_verified": "false"}},
        [],
    ],
)
def test_malformed_measurement_evidence_never_passes(payload: Any) -> None:
    result = validate_worker_result(payload)
    assert result["ok"] is False
    assert result["phase"] == "worker_protocol"


@pytest.mark.parametrize(
    "update",
    [
        {"timeout_s": float("inf")},
        {"max_workers": True},
        {"max_workers": "2"},
        {"options": []},
        {"typo": 1},
    ],
)
def test_compiler_targets_reject_invalid_settings(tmp_path: Path, update: dict[str, Any]) -> None:
    target = {
        "schema_version": 1,
        "target_id": "fake",
        "family": "test",
        "checker": "lassi_x.compatibility.checkers.fake:FakeChecker",
        "precisions": ["fp32"],
    }
    path = tmp_path / "target.yaml"
    path.write_text(yaml.safe_dump({**target, **update}))
    with pytest.raises(ValidationError):
        load_target(path)


@pytest.mark.asyncio
async def test_partial_academy_startup_closes_previously_created_resources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from academy.manager import Manager  # noqa: PLC0415

    from lassi_x.execution import context as context_module  # noqa: PLC0415
    from lassi_x.execution.academy import _resource_executor  # noqa: PLC0415

    data = minimal_config(tmp_path)
    data["execution"] = {"mode": "academy", "resources": {"first": {}, "second": {}}}
    executors: list[Any] = []
    make_executor = _resource_executor
    launch = Manager.launch
    calls = 0

    def executor(*args: Any, **kwargs: Any) -> Any:
        created = make_executor(*args, **kwargs)
        executors.append(created)
        return created

    async def launch_then_fail(self: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("second resource failed")
        return await launch(self, *args, **kwargs)

    monkeypatch.setattr(context_module, "_resource_executor", executor)
    monkeypatch.setattr(Manager, "launch", launch_then_fail)
    with pytest.raises(RuntimeError, match="second resource failed"):
        await asyncio.wait_for(
            ExecutionContext.start(RunConfig.model_validate(data), tmp_path),
            3,
        )
    assert len(executors) == 2
    assert all(executor._shutdown for executor in executors)


@pytest.mark.asyncio
async def test_real_worker_startup_timeout_reaps_process_and_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launches = fake_worker(monkeypatch, "import time; time.sleep(30)")
    monkeypatch.setattr("lassi_x.hermes.WORKER_SHUTDOWN_GRACE_S", 0.02)
    session = session_at(tmp_path, turn_timeout_s=0.03)
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(session.start(), 1)
    assert session._process is None
    assert session._stderr_task is None
    assert not Path(launches[0]["env"]["HERMES_HOME"]).exists()


@pytest.mark.asyncio
async def test_academy_file_io_does_not_block_heartbeat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import threading  # noqa: PLC0415

    from academy.exchange import LocalExchangeFactory  # noqa: PLC0415
    from academy.manager import Manager  # noqa: PLC0415

    from lassi_x.execution import workspace as workspace_ops  # noqa: PLC0415
    from lassi_x.execution.worker import ExecutionWorker  # noqa: PLC0415
    from lassi_x.protocol import FileGet  # noqa: PLC0415

    entered, release = threading.Event(), threading.Event()
    get_file = workspace_ops.get_file

    def slow_read(*args: Any, **kwargs: Any) -> Any:
        entered.set()
        release.wait(2)
        return get_file(*args, **kwargs)

    monkeypatch.setattr(workspace_ops, "get_file", slow_read)
    async with await Manager.from_exchange_factory(LocalExchangeFactory()) as manager:
        handle = await manager.launch(ExecutionWorker, args=(str(tmp_path),))
        await handle.put_file(FilePut(workspace="w", path="x", text="ok"))
        pending = asyncio.create_task(handle.get_file(FileGet(workspace="w", path="x")))
        try:
            async with asyncio.timeout(1):
                while not entered.is_set():
                    await asyncio.sleep(0.01)
            await asyncio.wait_for(handle.ping(), 0.2)
        finally:
            release.set()
            assert (await pending).content == "ok"


def test_persisted_candidate_rejects_wrong_nested_types() -> None:
    from lassi_x.types import Candidate  # noqa: PLC0415

    record = Candidate("c1", "test", None, "direct", Path("candidate.py")).to_dict()
    record["usage"]["input_tokens"] = "100"
    with pytest.raises(ValidationError):
        Candidate.from_dict(record)


def test_rejected_cross_field_assignment_preserves_valid_config() -> None:
    model = ModelConfig(model="test", api_key_env="API_KEY")
    with pytest.raises(ValidationError):
        model.claude_settings = Path("settings.json")
    assert model.api_key_env == "API_KEY"
    assert model.claude_settings is None


@pytest.mark.parametrize(
    "payload",
    [
        {"ok": True},
        {
            "ok": True,
            "median_s": 0.1,
            "min_s": 0.1,
            "timing": {"sample_count": 2, "samples_s": [0.1]},
        },
        {"ok": True, "median_s": 0.1, "min_s": 0.1, "timing": {"samples_s": [-0.1]}},
    ],
)
def test_incomplete_or_inconsistent_timing_is_protocol_failure(payload: Any) -> None:
    assert validate_worker_result(payload)["phase"] == "worker_protocol"


@pytest.mark.asyncio
async def test_concurrent_runs_keep_workspace_registrations_and_credentials_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.yaml").write_text("user_setting: preserved\n")
    (source / ".env").write_text("EXAMPLE_KEY=private-placeholder\n")
    monkeypatch.setenv("HERMES_HOME", str(source))
    config = RunConfig.model_validate(minimal_config(tmp_path))
    contexts: list[ExecutionContext] = []
    homes: list[Path] = []
    try:
        for name in ("first", "second"):
            context = await ExecutionContext.start(config, tmp_path / name)
            contexts.append(context)
            assert context.hermes_home is not None
            homes.append(context.hermes_home)
            context.register_workspace("c1")
        assert homes[0] != homes[1]
        for context, home in zip(contexts, homes, strict=True):
            entry = yaml.safe_load((home / "config.yaml").read_text())["mcp_servers"]["lassi-x-c1"]
            assert entry["url"] == context.runner.url
            assert not (home / ".env").exists()
        await contexts[0].close()
        assert (homes[1] / "config.yaml").exists()
        assert (source / "config.yaml").read_text() == "user_setting: preserved\n"
        assert not list((tmp_path / "first").rglob(".env"))
    finally:
        for context in contexts:
            await context.close()
    assert all(not home.exists() for home in homes)


def test_checkpoint_preserves_fixture_path_and_rejects_changed_oracle(tmp_path: Path) -> None:
    import hashlib  # noqa: PLC0415
    import json  # noqa: PLC0415

    import numpy as np  # noqa: PLC0415

    from lassi_x import pipeline  # noqa: PLC0415

    config = RunConfig.model_validate(minimal_config(tmp_path))
    oracle = tmp_path / "oracle.npy"
    np.save(oracle, np.asarray([1.0]))
    contract = tmp_path / "inputs.npz"
    payload = {
        "schema_version": 1,
        "config_sha256": pipeline._config_hash(config),
        "started_at": "2026-10-30T00:00:00+00:00",
        "oracle": {
            "output_path": str(oracle),
            "input_contract_path": str(contract),
            "output_sha256": hashlib.sha256(oracle.read_bytes()).hexdigest(),
        },
    }
    (tmp_path / "checkpoint.json").write_text(json.dumps(payload))
    state, _, _ = pipeline._load_checkpoint(tmp_path, config)
    assert state.oracle is not None
    assert state.oracle.input_contract_path == contract
    np.save(oracle, np.asarray([2.0]))
    with pytest.raises(ValueError, match="oracle checksum mismatch"):
        pipeline._load_checkpoint(tmp_path, config)


@pytest.mark.asyncio
async def test_exchange_cleanup_has_its_own_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    from academy.exchange import LocalExchangeFactory  # noqa: PLC0415
    from academy.manager import Manager  # noqa: PLC0415

    manager = await Manager.from_exchange_factory(LocalExchangeFactory())

    async def hang() -> None:
        await asyncio.sleep(30)

    try:
        with monkeypatch.context() as patch:
            patch.setattr("lassi_x.execution.context.SHUTDOWN_TIMEOUT_S", 0.02)
            patch.setattr(manager, "close", hang)
            patch.setattr(manager.exchange_client, "close", hang)
            await asyncio.wait_for(ExecutionContext._close_manager(manager), 0.2)
    finally:
        await manager.close()


def test_numeric_errors_are_typed_without_discarding_divergence() -> None:
    payload = {"ok": True, "median_s": 0.1, "min_s": 0.1, "metrics": {"relative_l2": "0.1"}}
    assert validate_worker_result(payload)["phase"] == "worker_protocol"
    payload["metrics"]["relative_l2"] = float("inf")  # type: ignore[index]
    assert validate_worker_result(payload)["ok"] is True
