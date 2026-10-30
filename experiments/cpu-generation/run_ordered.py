"""Run prepared CPU campaigns sequentially, optionally detached from the terminal.

Accepts any suite manifests, including campaigns prepared for OSS providers.
Re-running starts new attempts; this launcher does not resume interrupted runs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from suite import digest


def pending_kernels(path: Path, selected: list[str] | None) -> list[str]:
    """Exclude verified kernels and completed non-quota evaluations."""
    manifest = json.loads(path.read_text())
    pending = []
    for entry in manifest["entries"]:
        name = entry["name"]
        if selected and name not in selected:
            continue
        records = sorted((path.parent / "runs" / name).glob("*/run.json"))
        outcomes = [json.loads(record.read_text()) for record in records]
        if any(outcome.get("status") == "cpu_verified" for outcome in outcomes):
            continue
        if records:
            diagnostic = records[-1].read_text().lower()
            if not ("http 429" in diagnostic and "usage limit has been reached" in diagnostic):
                continue
        pending.append(name)
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", type=Path, nargs="+")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", nargs="+", help="Run only these kernels in each campaign")
    parser.add_argument(
        "--cooldown-s",
        type=float,
        default=0.0,
        help="Wait this many seconds between kernels within each campaign",
    )
    parser.add_argument(
        "--wait-for-quota",
        action="store_true",
        help="Retry quota-interrupted kernels until evaluated",
    )
    args = parser.parse_args()
    manifests = [path.resolve() for path in args.manifests]
    # Validate every campaign before consuming any model quota.
    for path in manifests:
        manifest = json.loads(path.read_text())
        for filename, expected in manifest["files"].items():
            if digest(Path(filename)) != expected:
                raise ValueError(f"Campaign input changed: {filename}")
    root = Path(__file__).resolve().parents[2]
    suite = Path(__file__).with_name("suite.py")
    executable = root / ".venv/bin/lassi-x"
    commands = [
        [
            sys.executable,
            "-u",
            str(suite),
            "run",
            str(path),
            "--execute",
            "--lassi-x",
            str(executable),
        ]
        for path in manifests
    ]
    if args.only:
        for command in commands:
            command.extend(["--only", *args.only])
    if args.cooldown_s:
        for command in commands:
            command.extend(["--cooldown-s", str(args.cooldown_s)])
    if not args.execute:
        for command in commands:
            print(subprocess.list2cmdline(command))
        return 0
    output = args.output.resolve()
    if args.detach:
        if output.exists():
            raise ValueError(f"Refusing to reuse launcher output: {output}")
        output.mkdir(parents=True)
        with (output / "launcher.log").open("x") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    str(Path(__file__).resolve()),
                    *map(str, manifests),
                    "--execute",
                    "--output",
                    str(output),
                    *(["--wait-for-quota"] if args.wait_for_quota else []),
                    *(["--only", *args.only] if args.only else []),
                    *(["--cooldown-s", str(args.cooldown_s)] if args.cooldown_s else []),
                ],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Started launcher PID {process.pid}; log: {output / 'launcher.log'}")
        return 0
    output.mkdir(parents=True, exist_ok=True)
    status_path = output / "status.json"
    if status_path.exists():
        raise ValueError(f"Refusing to overwrite launcher status: {status_path}")
    state = {
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "campaigns": [],
    }

    def save() -> None:
        status_path.write_text(json.dumps(state, indent=2) + "\n")

    save()
    failures = 0
    try:
        for path, command in zip(manifests, commands, strict=True):
            entry = {"manifest": str(path), "status": "running"}
            state["campaigns"].append(entry)
            save()
            print(f"Starting {path}", flush=True)
            while True:
                active_command = command
                if args.wait_for_quota:
                    pending = pending_kernels(path, args.only)
                    entry["pending_kernels"] = pending
                    save()
                    if not pending:
                        result = subprocess.CompletedProcess(command, 0)
                        break
                    active_command = (
                        command[: command.index("--only")] if "--only" in command else command[:]
                    )
                    active_command = [*active_command, "--only", *pending]
                result = subprocess.run(active_command, cwd=root, check=False)
                if result.returncode != 2 or not args.wait_for_quota:
                    break
                state["status"] = "waiting_for_quota"
                entry["status"] = "waiting_for_quota"
                entry["pending_kernels"] = pending_kernels(path, args.only)
                save()
                print("Quota exhausted; retrying unfinished kernels in 15 minutes", flush=True)
                # Short sleeps permit responsive interruption of this background worker.
                for _ in range(15):
                    time.sleep(60)
                state["status"] = "running"
                entry["status"] = "running"
                save()
            entry.update(status="finished", returncode=result.returncode)
            failures += result.returncode != 0
            save()
            if result.returncode == 2:
                state["status"] = "quota_exhausted"
                return 2
            if result.returncode == 3:
                state["status"] = "endpoint_unreachable"
                return 3
        state["status"] = "finished_with_failures" if failures else "finished"
    except BaseException:
        state["status"] = "interrupted"
        raise
    finally:
        save()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
