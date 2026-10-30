"""Resume saved numerical repairs, optionally after a detached delay."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from lassi_x.artifacts import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--delay-seconds", type=float, default=0)
    parser.add_argument("--not-before", type=float, help=argparse.SUPPRESS)
    args = parser.parse_args()
    campaign = args.campaign.resolve()
    if args.delay_seconds < 0:
        raise ValueError("delay must be nonnegative")
    if args.detach:
        deadline = time.time() + args.delay_seconds
        with (campaign / "numerical-retry.log").open("a") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    str(campaign),
                    "--not-before",
                    str(deadline),
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Numerical repair retry PID {process.pid}")
        print(f"Scheduled for {datetime.fromtimestamp(deadline, UTC).isoformat()}")
        print(f"Status: {campaign / 'numerical-retry-status.json'}")
        return 0
    entries = json.loads((campaign / "campaign.json").read_text())["entries"]
    pending_entries = []
    for entry in entries:
        root = campaign / entry["model"] / "runs" / entry["name"]
        checkpoint = sorted(root.glob("*/checkpoint.json"))[-1]
        state = json.loads(checkpoint.read_text())
        variants = state.get("compensation_variants", [])
        pending = any(
            variant["status"] == "crashed"
            or any(
                item["gate"] == "runtime"
                and "unsupported dataset" in item["message"]
                and "base-fp32.npy" in " ".join(item.get("command") or [])
                for item in variant.get("diagnostics", [])
            )
            for variant in variants
        )
        journals = (checkpoint.parent / "progress").glob("*.json")
        if pending or any(
            json.loads(p.read_text())["stage"] == "numerical_retry" for p in journals
        ):
            pending_entries.append(entry)
    entries = pending_entries
    state = {"pid": os.getpid(), "status": "running", "completed": [], "total": len(entries)}
    status_path = campaign / "numerical-retry-status.json"
    deadline = args.not_before if args.not_before is not None else time.time() + args.delay_seconds
    if deadline > time.time():
        state.update(
            status="scheduled", scheduled_for=datetime.fromtimestamp(deadline, UTC).isoformat()
        )
        write_json(status_path, state)
        while deadline > time.time():
            time.sleep(min(60, max(0, deadline - time.time())))
    state["status"] = "running"
    write_json(status_path, state)
    for entry in entries:
        root = campaign / entry["model"] / "runs" / entry["name"]
        run_dir = sorted(root.glob("*/checkpoint.json"))[-1].parent
        state["current"] = {
            "model": entry["model"],
            "kernel": entry["name"],
            "run_dir": str(run_dir),
        }
        write_json(status_path, state)
        result = subprocess.run(
            [
                str(Path(sys.executable).parent / "lassi-x"),
                "--log-level",
                "ERROR",
                "run",
                entry["config"],
                "--resume",
                str(run_dir),
                "--retry-numerical-repairs",
            ],
            check=False,
        )
        record = json.loads((run_dir / "run.json").read_text())
        state["completed"].append(
            {**state["current"], "returncode": result.returncode, "status": record.get("status")}
        )
        if record.get("error"):
            state.update(status="interrupted", error=record["error"])
            write_json(status_path, state)
            return 1
        write_json(status_path, state)
    state.update(status="finished", current=None)
    write_json(status_path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
