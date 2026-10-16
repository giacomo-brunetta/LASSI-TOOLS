"""Retry only provider-interrupted LARGE candidates; retain all completed work."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from lassi_x.artifacts import write_json
from lassi_x.interruptions import model_service_interrupted

REPO = Path(__file__).resolve().parents[2]
DEFAULT = REPO / "runs/a100-large-repair-20261015"


def reopen(run: Path) -> tuple[bool, bool]:
    checkpoint = run / "checkpoint.json"
    state = json.loads(checkpoint.read_text())
    pending = [c for c in state["candidates"] if model_service_interrupted(c)]
    repairs = any(model_service_interrupted(c) for c in state["compatibility_candidates"])
    if not pending and not repairs:
        return False, False
    # Current interrupted starting candidates never completed an initial model turn.
    # Do not silently regenerate a future interrupted candidate with paid edits.
    if any(c["turn_outcomes"] or c["usage"]["input_tokens"] for c in pending):
        raise RuntimeError(f"Starting-candidate edits require explicit recovery: {run}")
    archive = run / "quota-retry-history" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    archive.mkdir(parents=True)
    for name in ("checkpoint.json", "run.json", "summary.md"):
        if (run / name).exists():
            shutil.copy2(run / name, archive / name)
    ids = {c["candidate_id"] for c in pending}
    for cid in ids:
        journal = run / "progress" / f"{cid}.json"
        if journal.exists():
            shutil.move(str(journal), str(archive / journal.name))
    state["candidates"] = [c for c in state["candidates"] if c["candidate_id"] not in ids]
    state["completed_candidate_ids"] = [c for c in state["completed_candidate_ids"] if c not in ids]
    state["completed_stages"] = [
        s for s in state["completed_stages"] if s not in {"stream_candidates", "finalize"}
    ]
    write_json(checkpoint, state)
    return True, repairs


def execute(root: Path) -> int:
    plan = json.loads((root / "campaign.json").read_text())
    status = root / "retry-status.json"
    state = {
        "pid": os.getpid(),
        "status": "running",
        "started_at": datetime.now(UTC).isoformat(),
        "completed": [],
        "skipped": [],
    }
    write_json(status, state)
    for entry in plan["entries"]:
        run = sorted((root / entry["model"] / "runs" / entry["name"]).glob("*/checkpoint.json"))[
            -1
        ].parent
        checkpoint = json.loads((run / "checkpoint.json").read_text())
        pending = model_service_interrupted(checkpoint)
        # A previous retry may have reopened but not yet completed the stream.
        pending = pending or "stream_candidates" not in checkpoint["completed_stages"]
        if not pending:
            state["skipped"].append({"model": entry["model"], "name": entry["name"]})
            continue
        state["current"] = {"model": entry["model"], "name": entry["name"], "run": str(run)}
        write_json(status, state)
        try:
            _, repairs = reopen(run)
            command = [
                str(REPO / ".venv/bin/lassi-x"),
                "--log-level",
                "INFO",
                "run",
                entry["config"],
                "--resume",
                str(run),
            ]
            if repairs:
                command.append("--retry-interrupted-repairs")
            print(f"Resuming {entry['model']} {entry['name']} at {run}", flush=True)
            result = subprocess.run(command, cwd=REPO, check=False)
            record = json.loads((run / "run.json").read_text())
            saved = json.loads((run / "checkpoint.json").read_text())
            if (
                record.get("error")
                or model_service_interrupted(record)
                or model_service_interrupted(saved)
            ):
                raise RuntimeError(
                    "Service interruption; progress saved, no further experiments launched"
                )
            state["completed"].append(
                {**state["current"], "returncode": result.returncode, "status": record["status"]}
            )
            write_json(status, state)
        except Exception as exc:
            state.update(status="interrupted", error=str(exc))
            write_json(status, state)
            return 1
    state.update(status="finished", current=None, finished_at=datetime.now(UTC).isoformat())
    write_json(status, state)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    root = args.output.resolve()
    if args.detach:
        with (root / "retry.log").open("a") as log:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--output", str(root)],
                cwd=REPO,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Retry PID {process.pid}; {root / 'retry-status.json'}")
        return 0
    return execute(root)


if __name__ == "__main__":
    raise SystemExit(main())
