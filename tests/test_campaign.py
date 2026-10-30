"""Campaign handoffs, scientific failures and recovery must preserve provenance."""

from __future__ import annotations

import fcntl
import json
import shutil
import sys
from typing import TYPE_CHECKING, Any

import pytest
import yaml

from lassi_x.campaign import Campaign, Plan, StageContext, Verdict, command_campaign, prepare
from lassi_x.cli import build_parser

if TYPE_CHECKING:
    from pathlib import Path

WORKER = """
import json, os
from pathlib import Path
context = json.loads(Path(os.environ["LASSI_CAMPAIGN_CONTEXT"]).read_text())
task = context["task"]
Path("candidate.py").write_text("revision " + task["id"])
Path("evidence.json").write_text(json.dumps(context))
status = "failed" if task["id"] == "validate" and context["attempt"] == 1 else "passed"
Path(context["verdict_path"]).write_text(json.dumps({
    "status": status, "reason": "numerical comparison",
    "checks": [{"id": name, "status": status, "reason": "checked"} for name in task["checks"]]
}))
"""


def task(name: str = "generate", **kwargs: Any) -> dict[str, Any]:
    return {
        "id": name,
        "case": "three-mm-fp64",
        "stage": name,
        "command": [sys.executable, "{input:worker}"],
        "timeout_s": 10,
        "checks": ["unit-tests", "judge"],
        "max_attempts": 2,
        "inputs": {"worker": "files/worker"},
        "outputs": {
            "candidate": {"path": "candidate.py", "role": "candidate"},
            "evidence": {"path": "evidence.json", "role": "evidence"},
        },
        **kwargs,
    }


def campaign(tmp_path: Path, tasks: list[dict[str, Any]], worker: str = WORKER) -> Campaign:
    (tmp_path / "worker.py").write_text(worker)
    plan = {
        "name": "test-campaign",
        "methodology": "Fixed inputs and budgets",
        "protocol": {"dataset": "mini", "selection": "all candidates"},
        "files": {"worker": "worker.py"},
        "tasks": tasks,
    }
    source = tmp_path / "campaign.yaml"
    source.write_text(yaml.safe_dump(plan))
    root = tmp_path / "results"
    prepare(source, root)
    return Campaign(root)


def dependent(name: str, parent: str, accepted: list[str] | None = None) -> dict[str, Any]:
    return task(
        name,
        dependencies={parent: accepted or ["passed"]},
        inputs={"worker": "files/worker", "parent": f"{parent}/candidate"},
    )


def test_frozen_handoff_and_continuation_do_not_repeat_work(tmp_path: Path) -> None:
    run = campaign(tmp_path, [task(), dependent("adapt", "generate")])
    # Original working files cease to be dependencies after preparation.
    (tmp_path / "worker.py").unlink()
    run.run()
    run.run()
    for item in run.frozen.plan.tasks:
        assert len(run.attempts(item)) == 1
    generate, adapt = [run.latest(item) for item in run.frozen.plan.tasks]
    assert generate and adapt
    assert generate.status == adapt.status == "passed"
    candidate = adapt.outputs["candidate"]
    assert candidate.parents["parent"] == generate.outputs["candidate"].sha256
    assert run.read_artifact(generate.outputs["candidate"]) == b"revision generate"
    assert run.read_artifact(candidate) == b"revision adapt"
    assert len(run.summary()["tasks"]) == 2  # type: ignore[arg-type]


def test_failure_blocks_measurement_but_allows_explicit_repair_branch(tmp_path: Path) -> None:
    run = campaign(
        tmp_path,
        [
            task("validate"),
            dependent("measure", "validate"),
            dependent("repair", "validate", ["failed"]),
        ],
    )
    run.run()
    records = [run.latest(item) for item in run.frozen.plan.tasks]
    assert records[0] and records[0].status == "failed"
    assert records[1] is None
    assert records[2] and records[2].status == "passed"
    summary = json.dumps(run.summary())
    assert '"blocked"' in summary and '"measure"' in summary
    with pytest.raises(ValueError, match="downstream attempts"):
        run.run(retry="validate")


def test_retry_is_explicit_bounded_and_preserves_prior_failure(tmp_path: Path) -> None:
    run = campaign(tmp_path, [task("validate"), dependent("measure", "validate")])
    run.run()
    run.run()
    validation = run.frozen.plan.tasks[0]
    assert len(run.attempts(validation)) == 1
    run.run(retry="validate")
    # Retry executes precisely the requested task; continuation is a separate action.
    assert run.latest(run.frozen.plan.tasks[1]) is None
    assert len(run.attempts(validation)) == 2
    previous = json.loads((run.attempts(validation)[0] / "result.json").read_text())
    assert previous["status"] == "failed"
    run.run()
    assert run.latest(run.frozen.plan.tasks[1]) is not None
    with pytest.raises(ValueError, match="failed or incomplete"):
        run.run(retry="validate")


@pytest.mark.parametrize(
    "worker,reason",
    [
        ("pass", "FileNotFoundError"),
        (WORKER + "\nraise SystemExit(2)\n", "exited 2"),
        (WORKER + '\nPath("candidate.py").unlink()\n', "omitted output"),
        (
            WORKER.replace('for name in task["checks"]', 'for name in task["checks"][:1]'),
            "planned checks",
        ),
        (
            WORKER + '\nPath(context["inputs"]["worker"]["local_path"]).write_text("changed")\n',
            "modified input",
        ),
    ],
)
def test_exit_success_and_partial_evidence_cannot_bypass_gate(
    tmp_path: Path,
    worker: str,
    reason: str,
) -> None:
    run = campaign(tmp_path, [task(), dependent("measure", "generate")], worker)
    run.run()
    result = run.latest(run.frozen.plan.tasks[0])
    assert result and result.status == "incomplete"
    assert reason in result.reason
    assert {check.id for check in result.checks} == {"unit-tests", "judge"}
    assert run.latest(run.frozen.plan.tasks[1]) is None


def test_timeout_and_retry_budget(tmp_path: Path) -> None:
    run = campaign(tmp_path, [task(timeout_s=0.1)], "import time; time.sleep(10)")
    run.run()
    result = run.latest(run.frozen.plan.tasks[0])
    assert result and result.status == "incomplete" and "TimeoutExpired" in result.reason
    assert all(check.status == "inconclusive" for check in result.checks)
    run.run(retry="generate")
    with pytest.raises(ValueError, match="budget exhausted"):
        run.run(retry="generate")


@pytest.mark.parametrize("partial_commit", [False, True])
def test_interrupted_attempt_requires_retry(tmp_path: Path, partial_commit: bool) -> None:
    run = campaign(tmp_path, [task()])
    interrupted = run.root / "tasks/generate/000001"
    interrupted.mkdir(parents=True)
    if partial_commit:
        (interrupted / "result.json").write_text("partially committed evidence")
    run.run()
    assert not (interrupted / "result.sha256").exists()
    incomplete = run.latest(run.frozen.plan.tasks[0])
    assert incomplete and all(check.status == "inconclusive" for check in incomplete.checks)
    run.run(retry="generate")
    result = run.latest(run.frozen.plan.tasks[0])
    assert result and result.status == "passed" and result.number == 2


@pytest.mark.parametrize("target", ["input", "artifact", "plan", "record"])
def test_changed_evidence_is_rejected(tmp_path: Path, target: str) -> None:
    run = campaign(tmp_path, [task()])
    run.run()
    result = run.latest(run.frozen.plan.tasks[0])
    assert result
    paths = {
        "input": run.root / run.frozen.files["worker"].path,
        "artifact": run.root / result.outputs["candidate"].path,
        "plan": run.root / "plan.json",
        "record": run.root / "tasks/generate/000001/result.json",
    }
    paths[target].write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        Campaign(run.root).summary()


def test_single_writer_and_running_status(tmp_path: Path) -> None:
    run = campaign(tmp_path, [task()])
    with (run.root / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (run.root / "active.json").write_text('{"task": "generate"}')
        assert '"running"' in json.dumps(run.summary())
        with pytest.raises(ValueError, match="another runner"):
            run.run()


def test_cross_campaign_import_pins_attempt_and_survives_source_removal(tmp_path: Path) -> None:
    origin = campaign(tmp_path, [task("validate")])
    origin.run()
    origin.run(retry="validate")
    source = tmp_path / "followup.yaml"
    plan = origin.frozen.plan.model_dump()
    plan["name"] = "followup"
    plan["files"]["baseline"] = {
        "campaign": "results",
        "task": "validate",
        "attempt": 1,
        "output": "candidate",
    }
    plan["tasks"] = [dependent("adapt", "validate")]
    plan["tasks"][0]["dependencies"] = {}
    plan["tasks"][0]["inputs"]["parent"] = "files/baseline"
    source.write_text(yaml.safe_dump(plan))
    destination = tmp_path / "followup"
    with pytest.raises(ValueError, match="not eligible"):
        prepare(source, destination)
    # Explicitly select the failed revision as an unverified seed, never 'latest'.
    plan["files"]["baseline"]["accept"] = ["failed"]
    source.write_text(yaml.safe_dump(plan))
    prepare(source, destination)
    frozen = Campaign(destination)
    baseline = frozen.frozen.files["baseline"]
    assert baseline.role == "candidate" and baseline.parents
    assert any("/validate/1/candidate" in parent for parent in baseline.parents)
    shutil.rmtree(origin.root)
    frozen.run()
    result = frozen.latest(frozen.frozen.plan.tasks[0])
    assert result and result.status == "passed"


@pytest.mark.parametrize(
    "changes",
    [
        {"dependencies": {"unknown": ["passed"]}},
        {"dependencies": {"generate": ["passed"]}},
        {"inputs": {"worker": "files/missing"}},
        {"outputs": {"candidate": {"path": "../candidate.py", "role": "candidate"}}},
        {"checks": ["judge", "judge"]},
        {"command": ["{input:missing}"]},
    ],
)
def test_bad_plans_fail_before_creating_campaign(tmp_path: Path, changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        campaign(tmp_path, [task(**changes)])
    assert not (tmp_path / "results").exists()


def test_positive_verdict_requires_all_checks_and_unique_ids() -> None:
    for checks in [
        [{"id": "suite", "status": "failed", "reason": "mismatch"}],
        [{"id": "suite", "status": "passed", "reason": "ok"}] * 2,
    ]:
        with pytest.raises(ValueError):
            Verdict(status="passed", reason="done", checks=checks)


def test_incomplete_stage_preserves_passed_and_unfinished_checks(tmp_path: Path) -> None:
    worker = (
        WORKER
        + """
Path(context["verdict_path"]).write_text(json.dumps({
    "status": "incomplete", "reason": "judge unavailable",
    "checks": [
        {"id": "unit-tests", "status": "passed", "reason": "All 12 passed"},
        {"id": "judge", "status": "inconclusive", "reason": "provider timed out"}
    ]
}))
"""
    )
    run = campaign(tmp_path, [task(), dependent("measure", "generate")], worker)
    run.run()
    result = run.latest(run.frozen.plan.tasks[0])
    assert result and result.status == "incomplete"
    assert [check.status for check in result.checks] == ["passed", "inconclusive"]
    assert run.latest(run.frozen.plan.tasks[1]) is None


def test_cli_failure_exit_and_status_keep_all_cases(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run = campaign(tmp_path, [task("validate"), dependent("measure", "validate")])
    parser = build_parser()
    assert command_campaign(parser.parse_args(["campaign", "run", str(run.root)])) == 1
    summary = json.loads(capsys.readouterr().out)
    assert [row["status"] for row in summary["tasks"]] == ["failed", "blocked"]
    assert (
        command_campaign(
            parser.parse_args(
                [
                    "campaign",
                    "retry",
                    str(run.root),
                    "--task",
                    "validate",
                ]
            )
        )
        == 1
    )
    capsys.readouterr()
    assert command_campaign(parser.parse_args(["campaign", "run", str(run.root)])) == 0
    summary = json.loads(capsys.readouterr().out)
    assert [row["status"] for row in summary["tasks"]] == ["passed", "passed"]


def test_cli_and_stage_interface(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    args = build_parser().parse_args(["campaign", "retry", "runs/new", "--task", "validate"])
    assert args.task == "validate"
    run = campaign(tmp_path, [task()])
    run.run()
    context_path = run.root / "tasks/generate/000001/context.json"
    monkeypatch.setenv("LASSI_CAMPAIGN_CONTEXT", str(context_path))
    context = StageContext.load()
    assert context.input_path("worker").read_text() == WORKER
    with pytest.raises(ValueError, match="every planned check"):
        context.finish(
            Verdict.model_validate(
                {
                    "status": "passed",
                    "reason": "done",
                    "checks": [{"id": "unit-tests", "status": "passed", "reason": "ok"}],
                }
            )
        )
    assert Plan.model_validate(run.frozen.plan.model_dump()) == run.frozen.plan
