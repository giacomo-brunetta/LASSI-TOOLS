"""Resume interrupted compatibility repairs sequentially; stop on renewed interruption."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from lassi_x.artifacts import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    campaign = args.campaign.resolve()
    status_path = campaign / "repair-retry-status.json"
    if args.detach:
        with (campaign / "repair-retry.log").open("a") as log:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), str(campaign)],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Repair retry launcher PID {process.pid}; status: {status_path}")
        return 0
    manifest = json.loads((campaign / "campaign.json").read_text())
    jobs = []
    for entry in manifest["entries"]:
        checkpoints = sorted((campaign / "runs" / entry["name"]).glob("*/checkpoint.json"))
        if not checkpoints:
            continue
        checkpoint = checkpoints[-1]
        payload = json.loads(checkpoint.read_text())
        pending = [
            item
            for item in payload.get("compatibility_candidates", [])
            if item["status"] == "crashed"
        ]
        if pending:
            jobs.append(
                {
                    "kernel": entry["name"],
                    "run_dir": str(checkpoint.parent),
                    "config": str(campaign / entry["config"]),
                    "repairs": len(pending),
                }
            )
    state = {"status": "running", "pid": os.getpid(), "jobs": jobs, "completed": []}
    write_json(status_path, state)
    for job in jobs:
        state["current"] = job
        write_json(status_path, state)
        result = subprocess.run(
            [
                str(Path(sys.executable).parent / "lassi-x"),
                "--log-level",
                "ERROR",
                "run",
                job["config"],
                "--resume",
                job["run_dir"],
                "--retry-interrupted-repairs",
            ],
            check=False,
        )
        payload = json.loads((Path(job["run_dir"]) / "checkpoint.json").read_text())
        interrupted = any(
            item["status"] == "crashed" for item in payload.get("compatibility_candidates", [])
        )
        state["completed"].append({**job, "returncode": result.returncode})
        if interrupted:
            state["status"] = "interrupted"
            write_json(status_path, state)
            return 1
        write_json(status_path, state)
    state.update(status="finished", current=None)
    write_json(status_path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
